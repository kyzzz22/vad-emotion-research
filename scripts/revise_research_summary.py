from copy import deepcopy
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt
from lxml import etree
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "研究概要書_JIANGXIJIE_MA26006_原稿.docx"
INTERMEDIATE = ROOT / ".docx_qa" / "研究概要書_JIANGXIJIE_MA26006_改訂中.docx"
OUTPUT = ROOT / "研究概要書_JIANGXIJIE_MA26006_修正版.docx"
PLOT = ROOT / ".docx_qa" / "image1_revised.png"
FULL_JAPANESE_FONT = ROOT / ".docx_qa" / "HiraginoMinchoProN-W3.ttf"
FULL_JAPANESE_FONT_NAME = "Hiragino Mincho ProN W3"
FONT_GUID = "A27E2D4C-7F9B-4A5F-9C23-18D4A6B7E901"
FONT_REL_ID = "rIdArialUnicodeFull"
FONT_TARGET = "fonts/hiragino_mincho_full.odttf"


def replace_paragraph(paragraph, text):
    """Replace paragraph text while retaining its first run's character format."""
    rpr = None
    if paragraph.runs and paragraph.runs[0]._r.rPr is not None:
        rpr = deepcopy(paragraph.runs[0]._r.rPr)
    for run in list(paragraph.runs):
        paragraph._p.remove(run._r)
    run = paragraph.add_run(text)
    if rpr is not None:
        run._r.insert(0, rpr)


def replace_labeled_paragraph(paragraph, label, text):
    """Retain the original inline subheading/body distinction."""
    bold_rpr = None
    body_rpr = None
    if paragraph.runs:
        if paragraph.runs[0]._r.rPr is not None:
            bold_rpr = deepcopy(paragraph.runs[0]._r.rPr)
        if len(paragraph.runs) > 1 and paragraph.runs[1]._r.rPr is not None:
            body_rpr = deepcopy(paragraph.runs[1]._r.rPr)
    for run in list(paragraph.runs):
        paragraph._p.remove(run._r)
    label_run = paragraph.add_run(label)
    if bold_rpr is not None:
        label_run._r.insert(0, bold_rpr)
    body_run = paragraph.add_run(text)
    if body_rpr is not None:
        body_run._r.insert(0, body_rpr)


def replace_title(paragraph):
    rpr = deepcopy(paragraph.runs[0]._r.rPr)
    for run in list(paragraph.runs):
        paragraph._p.remove(run._r)
    for index, text in enumerate(
        [
            "感情語VADは誘発情動体験へどこまで適用できるか",
            "\n― NRC-VADとDREAMERのクロスコンテクスト比較 ―",
        ]
    ):
        run = paragraph.add_run(text)
        run._r.insert(0, deepcopy(rpr))


def normalize_japanese(paragraph, font_name, font_size=None, exact_line=None):
    """Prevent inherited zh-CN language metadata from disrupting Japanese layout."""
    ppr = paragraph._p.get_or_add_pPr()
    paragraph_rpr = ppr.find(qn("w:rPr"))
    if paragraph_rpr is None:
        paragraph_rpr = OxmlElement("w:rPr")
        ppr.append(paragraph_rpr)
    p_lang = paragraph_rpr.find(qn("w:lang"))
    if p_lang is None:
        p_lang = OxmlElement("w:lang")
        paragraph_rpr.append(p_lang)
    p_lang.set(qn("w:eastAsia"), "ja-JP")
    for run in paragraph.runs:
        rpr = run._r.get_or_add_rPr()
        fonts = rpr.find(qn("w:rFonts"))
        if fonts is None:
            fonts = OxmlElement("w:rFonts")
            rpr.insert(0, fonts)
        for key in ("ascii", "eastAsia", "hAnsi", "cs"):
            fonts.set(qn(f"w:{key}"), font_name)
        lang = rpr.find(qn("w:lang"))
        if lang is None:
            lang = OxmlElement("w:lang")
            rpr.append(lang)
        lang.set(qn("w:val"), "ja-JP")
        lang.set(qn("w:eastAsia"), "ja-JP")
        if font_size is not None:
            run.font.size = Pt(font_size)
    if exact_line is not None:
        paragraph.paragraph_format.line_spacing = Pt(exact_line)


def revise_plot(source_docx):
    with ZipFile(source_docx) as archive:
        image_bytes = archive.read("word/media/image1.png")
    temp_original = ROOT / ".docx_qa" / "image1_original.png"
    temp_original.write_bytes(image_bytes)
    image = Image.open(temp_original).convert("RGBA")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf", 20
    )
    panels = [
        (75, 430, "r=.875, slope=.520, Holm p=.018"),
        (610, 965, "r=.832, slope=.341, Holm p=.034"),
        (1145, 1500, "r=-.121, slope=-.055, Holm p=.792"),
    ]
    for left, right, label in panels:
        draw.rectangle((left, 112, right, 143), fill="white")
        bbox = draw.textbbox((0, 0), label, font=font)
        width = bbox[2] - bbox[0]
        x = left + max(0, (right - left - width) // 2)
        draw.text((x, 114), label, font=font, fill="black")
    image.save(PLOT)


def patch_media(input_docx, output_docx):
    font_key = bytes.fromhex(FONT_GUID.replace("-", ""))[::-1]
    font_data = bytearray(FULL_JAPANESE_FONT.read_bytes())
    for index in range(min(32, len(font_data))):
        font_data[index] ^= font_key[index % 16]

    temp = output_docx.with_suffix(".tmp.docx")
    with ZipFile(input_docx, "r") as src, ZipFile(
        temp, "w", compression=ZIP_DEFLATED
    ) as dst:
        for item in src.infolist():
            if item.filename == "word/media/image1.png":
                data = PLOT.read_bytes()
            elif item.filename == "word/fontTable.xml":
                root = etree.fromstring(src.read(item.filename))
                ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
                existing = root.xpath(
                    f".//w:font[@w:name='{FULL_JAPANESE_FONT_NAME}']", namespaces=ns
                )
                if existing:
                    font = existing[0]
                else:
                    font = etree.SubElement(root, qn("w:font"))
                    font.set(qn("w:name"), FULL_JAPANESE_FONT_NAME)
                for child in list(font):
                    if etree.QName(child).localname.startswith("embed"):
                        font.remove(child)
                alt = etree.SubElement(font, qn("w:altName"))
                alt.set(qn("w:val"), "ヒラギノ明朝 ProN W3")
                family = etree.SubElement(font, qn("w:family"))
                family.set(qn("w:val"), "swiss")
                pitch = etree.SubElement(font, qn("w:pitch"))
                pitch.set(qn("w:val"), "variable")
                embedded = etree.SubElement(font, qn("w:embedRegular"))
                embedded.set(qn("r:id"), FONT_REL_ID)
                embedded.set(qn("w:fontKey"), "{" + FONT_GUID + "}")
                data = etree.tostring(
                    root, xml_declaration=True, encoding="UTF-8", standalone=True
                )
            elif item.filename == "word/_rels/fontTable.xml.rels":
                root = etree.fromstring(src.read(item.filename))
                rel_ns = "http://schemas.openxmlformats.org/package/2006/relationships"
                for rel in list(root):
                    if rel.get("Id") == FONT_REL_ID:
                        root.remove(rel)
                rel = etree.SubElement(root, f"{{{rel_ns}}}Relationship")
                rel.set("Id", FONT_REL_ID)
                rel.set(
                    "Type",
                    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/font",
                )
                rel.set("Target", FONT_TARGET)
                data = etree.tostring(
                    root, xml_declaration=True, encoding="UTF-8", standalone=True
                )
            elif item.filename == "[Content_Types].xml":
                root = etree.fromstring(src.read(item.filename))
                ct_ns = "http://schemas.openxmlformats.org/package/2006/content-types"
                part_name = "/word/" + FONT_TARGET
                for override in list(root):
                    if override.get("PartName") == part_name:
                        root.remove(override)
                override = etree.SubElement(root, f"{{{ct_ns}}}Override")
                override.set("PartName", part_name)
                override.set(
                    "ContentType",
                    "application/vnd.openxmlformats-officedocument.obfuscatedFont",
                )
                data = etree.tostring(
                    root, xml_declaration=True, encoding="UTF-8", standalone=True
                )
            else:
                data = src.read(item.filename)
            dst.writestr(item, data)
        dst.writestr("word/" + FONT_TARGET, bytes(font_data))
    temp.replace(output_docx)


def main():
    doc = Document(SOURCE)
    p = doc.paragraphs

    replace_title(p[0])
    replace_paragraph(
        p[5],
        "VADを用いれば，感情語の意味と刺激によって生じた情動体験を共通の座標空間に配置できる．"
        "このため，感情語辞書のVAD値を情動体験の教師値や参照値に利用することが考えられる．"
        "しかし，前者は語の一般的意味を判断するのに対し，後者は特定刺激下で自己が経験した情動を報告する[5，6]．"
        "両者は同じ尺度名を用いても測定対象が異なるため，辞書VADの情動体験への移送可能性は自明ではない．",
    )
    replace_paragraph(
        p[6],
        "NRC-VADとDREAMER・CASEは独立に整備されている[2-4]．"
        "そのため，各データセット単独の妥当性から，同じ感情カテゴリー名を介したクロスコンテクストの移送可能性は判断できない．"
        "特に，線形傾向，カテゴリーの順位，値の広がりがVAD各次元でどこまで保たれるかは検証されていない．",
    )
    replace_paragraph(
        p[7],
        "また，高い相関があっても値が縮小していれば，相互に置き換えることはできない．"
        "そこで本研究は，「対応するか」だけでなく「どの次元をどの条件で利用できるか」を問う．"
        "異種VADデータを段階的に比較する枠組みを示し，感情辞書を教師値や評価基準として利用する際の適用範囲と限界を判断できる基盤を提供する．",
    )
    replace_paragraph(
        p[9],
        "以上から，NRC-VADとDREAMERに共通する9感情カテゴリーを対象に，"
        "感情語の意味的評価が映像による情動体験へどこまで移送可能かをV・A・D別に明らかにする．"
        "具体的には，相対構造が保たれる次元，較正が必要な次元，再測定が必要な次元を識別する．"
        "なお，両評価の同一性や無条件の代替可能性は前提としない．",
    )
    replace_paragraph(p[10], "3 クロスコンテクスト比較枠組み")
    replace_paragraph(
        p[11],
        "共通する感情カテゴリー名を対応づけ，尺度範囲を[-1，1]に統一する．"
        "次に，①線形傾向，②順位，③値の広がりの3段階で次元別に比較する．"
        "これにより，「関連があること」「相対構造が保たれること」「同じ値として利用できること」を区別する．",
    )
    replace_paragraph(p[12], "4 分析方法（二次データ分析）")
    replace_labeled_paragraph(
        p[13],
        "4.1 分析方針　",
        "本枠組みを9感情カテゴリーに適用する．主要な判断にはVADを含むDREAMERを用いる．"
        "CASEはVAのみで共通カテゴリーも少ないため，処理手順の補足確認に限定する．",
    )
    replace_labeled_paragraph(
        p[14],
        "4.2 対象データ　",
        "NRC-VADではDREAMERのラベルと同名の英語名詞1語を参照値とし，形容詞でも感度分析した[3]．"
        "DREAMERでは23名×18映像＝414試行を9カテゴリー（各2映像）に集約した[2]．"
        "CASEは30名×8映像を含むが，共通カテゴリーは4つでDもない[4]．",
    )
    replace_paragraph(p[15], "4.3 分析手順")
    replace_paragraph(
        p[16],
        "各値を[-1，1]に変換し，試行をカテゴリー水準に集約した．"
        "線形傾向をPearson相関，順位対応をSpearman相関，値の広がりを回帰傾きで評価した．"
        "推測単位が少ないことを考慮し，正確置換検定，多重比較補正，参加者と映像を再抽出する階層bootstrapにより結果の頑健性を確認した．",
    )
    replace_paragraph(
        p[18],
        "3段階で比較した結果，Valenceでは線形対応と順位対応の双方が得られた．"
        "Arousalでは線形対応のみが得られ，Dominanceではいずれの対応も得られなかった（図1，表1）．"
        "すなわち，感情語VADの情動体験への移送可能性は次元依存的であった．",
    )
    replace_paragraph(
        p[21],
        "図1　意味的評価と情動体験評価のクロスコンテクスト対応（9感情カテゴリー）",
    )
    replace_paragraph(
        p[23],
        "表1　VAD次元別の対応と尺度差（9感情カテゴリー）",
    )
    replace_paragraph(
        p[26],
        "線形対応が得られたVとAの回帰傾きは，Valenceで.520，Arousalで.341であり，いずれも1より小さかった（表1）．"
        "したがって，情動体験評価は意味的評価より中立点付近に集まり，高い相関があっても数値は一致しない．"
        "ただし，回帰傾きは値の広がりの近似であり，尺度，刺激，標本の影響を個別には分離できない．"
        "形容詞による感度分析でもV・Aの線形対応とDの判断は変わらなかった．"
        "CASEにも同じ処理を適用できたが，4カテゴリーのため主要結果の再現性は判断しない．",
    )
    replace_paragraph(
        p[28],
        "Valenceでは線形対応と順位対応がともに強く，カテゴリー間の相対構造は比較的保たれた．"
        "一方，回帰傾きは.520であった．"
        "したがって，語彙的評価は情動体験の快・不快の方向を参照する用途には利用できるが，強度を含む代替値として用いるには較正が必要である．",
    )
    replace_paragraph(
        p[29],
        "ArousalではPearson相関が高い一方，Spearman相関は有意でなく，bootstrap区間もValenceより広かった．"
        "少数カテゴリーが線形傾向を支え，順位は安定していない可能性がある．"
        "このため，Arousalの移送可能性は部分的であり，別の刺激集合での再検証を要する．",
    )
    replace_paragraph(
        p[30],
        "Dominanceでは線形対応も順位対応も得られず，共通構造は支持されなかった．"
        "語彙的Dominanceが感情概念に含まれる強さや支配性，典型的な主体の力を捉えるのに対し，"
        "体験評価は視聴者自身の制御可能性，主体性，自己決定感に左右される可能性がある．"
        "すなわち，概念・典型場面・自己体験の評価対象のずれが対応を弱めたと考えられるが，本分析はこの機序を直接検証していない．",
    )
    replace_paragraph(
        p[32],
        "感情語VADの情動体験への移送可能性は次元ごとに異なった．"
        "Valenceは相対構造を保つが尺度較正を要し，Arousalは部分的，Dominanceは再測定を要する．"
        "したがって，辞書VADを教師値や評価基準に用いる際は，次元別に妥当性を確認し，対象データに合わせて較正する必要がある．"
        "本研究は，意味的評価と情動体験評価を橋渡しする比較枠組みと，その適用範囲を判断する設計指針を提示した．",
    )
    replace_paragraph(
        p[34],
        "本分析は9カテゴリー，名詞1語，各2映像に限られ，辞書全体や多様な刺激には一般化できない．"
        "また，データセット間で参加者と課題が異なるため，個人内対応を判断できない．"
        "CASEも4カテゴリーのVAのみであり，外的再現の検証には不十分である．",
    )
    replace_paragraph(
        p[35],
        "今後は3段階で進める．第1段階ではDREAMERのDominanceのSAM画面と教示文を確認し，測定定義を精査する．"
        "第2段階では感情数，映像数，類義語を増やし，外部データで次元別判断を再検証する．"
        "第3段階では同一参加者が感情語の意味，典型場面，映像後の自己体験を評価する実験を行い，"
        "語彙―典型場面―誘発体験間の個人内移送可能性を検証する．",
    )

    # More formal table label.
    replace_paragraph(doc.tables[0].cell(5, 0).paragraphs[0], "総合判断")

    body_indexes = [4, 5, 6, 7, 9, 11, 13, 14, 16, 18, 26, 28, 29, 30, 32, 34, 35]
    heading_indexes = [3, 8, 10, 12, 15, 17, 25, 27, 31, 33, 36]
    caption_indexes = [21, 23]
    normalize_japanese(p[0], FULL_JAPANESE_FONT_NAME, font_size=14, exact_line=14)
    for index in body_indexes:
        normalize_japanese(
            p[index], FULL_JAPANESE_FONT_NAME, font_size=9, exact_line=10.2
        )
    for index in heading_indexes:
        normalize_japanese(
            p[index], FULL_JAPANESE_FONT_NAME, font_size=10.5, exact_line=11
        )
    for index in caption_indexes:
        normalize_japanese(
            p[index], FULL_JAPANESE_FONT_NAME, font_size=9.5, exact_line=10.5
        )
    normalize_japanese(
        doc.tables[0].cell(5, 0).paragraphs[0],
        FULL_JAPANESE_FONT_NAME,
        font_size=9.5,
        exact_line=10.5,
    )

    INTERMEDIATE.parent.mkdir(parents=True, exist_ok=True)
    doc.save(INTERMEDIATE)
    revise_plot(INTERMEDIATE)
    patch_media(INTERMEDIATE, OUTPUT)


if __name__ == "__main__":
    main()
