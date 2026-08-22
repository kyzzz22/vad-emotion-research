#!/usr/bin/env python3
"""Build the VAD research summary by patching the AL20018 DOCX template."""

from __future__ import annotations

import io
import math
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from lxml import etree
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = Path("/Users/mac/Downloads/研究室/EMB相关/AL20018_概要.docx")
OUT = ROOT / "paper" / "研究概要書_JIANGXIJIE_MA26006_AL20018様式最終版.docx"
TMP = ROOT / ".codex_tmp" / "al20018_template"
FIG_DIR = TMP / "figures"
SUMMARY_CSV = ROOT / "public_data" / "dreamer_pilot" / "results" / "dreamer_category_summary.csv"

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "pic": "http://schemas.openxmlformats.org/drawingml/2006/picture",
    "cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties",
    "dc": "http://purl.org/dc/elements/1.1/",
    "dcterms": "http://purl.org/dc/terms/",
}
W = f"{{{NS['w']}}}"


def japanese_font() -> fm.FontProperties:
    candidates = [
        Path("/System/Library/Fonts/ヒラギノ明朝 ProN.ttc"),
        Path("/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc"),
        Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return fm.FontProperties(fname=str(path))
    return fm.FontProperties(family="sans-serif")


JP = japanese_font()
LATIN = fm.FontProperties(family="Times New Roman")


def save_figure(fig: plt.Figure, path: Path, width_px: int, height_px: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    dpi = 300
    fig.set_size_inches(width_px / dpi, height_px / dpi)
    fig.savefig(path, dpi=dpi, facecolor="white", bbox_inches=None, pad_inches=0.02)
    plt.close(fig)


def make_flow_figure(path: Path) -> None:
    fig, ax = plt.subplots()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    boxes = [
        (0.02, 0.22, 0.19, 0.56, "#EAF2F8", "意味的評価\nNRC-VAD"),
        (0.275, 0.22, 0.19, 0.56, "#F4F6F7", "共通9カテゴリー\n尺度を[-1,1]化"),
        (0.53, 0.22, 0.19, 0.56, "#FDEBD0", "情動体験評価\nDREAMER"),
        (0.785, 0.22, 0.19, 0.56, "#E8F8F5", "V・A・D別\n対応特性"),
    ]
    for x, y, w, h, color, text in boxes:
        patch = FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.012,rounding_size=0.025",
            linewidth=0.9,
            edgecolor="#333333",
            facecolor=color,
        )
        ax.add_patch(patch)
        ax.text(
            x + w / 2,
            y + h / 2,
            text,
            ha="center",
            va="center",
            fontsize=7.8,
            fontproperties=JP,
            linespacing=1.25,
        )
    for x1, x2 in [(0.215, 0.27), (0.47, 0.525), (0.725, 0.78)]:
        ax.add_patch(
            FancyArrowPatch(
                (x1, 0.5),
                (x2, 0.5),
                arrowstyle="-|>",
                mutation_scale=10,
                linewidth=0.9,
                color="#333333",
            )
        )
    save_figure(fig, path, 1600, 448)


def noun_data() -> pd.DataFrame:
    df = pd.read_csv(SUMMARY_CSV)
    out = df[(df["term_set"] == "noun") & (df["dominance_orientation"] == "reported")].copy()
    order = [
        "happiness",
        "amusement",
        "anger",
        "calmness",
        "surprise",
        "excitement",
        "fear",
        "disgust",
        "sadness",
    ]
    return out.set_index("emotion").loc[order].reset_index()


JP_LABEL = {
    "happiness": "幸福",
    "amusement": "愉快",
    "anger": "怒り",
    "calmness": "平静",
    "surprise": "驚き",
    "excitement": "興奮",
    "fear": "恐怖",
    "disgust": "嫌悪",
    "sadness": "悲しみ",
}


def add_scatter(
    ax: plt.Axes,
    df: pd.DataFrame,
    dim: str,
    title: str,
    r_value: float,
    p_value: float,
    slope: float,
    label_points: bool,
) -> None:
    x = df[f"{dim}_nrc"].to_numpy()
    y = df[f"{dim}_elicited_mean"].to_numpy()
    ax.scatter(x, y, s=18, color="#111111", edgecolors="white", linewidths=0.4, zorder=3)
    fit = np.polyfit(x, y, 1)
    grid = np.linspace(-1, 1, 100)
    ax.plot(grid, fit[0] * grid + fit[1], color="#111111", linewidth=1.1, zorder=2)
    ax.plot(grid, grid, color="#AAAAAA", linewidth=0.8, linestyle="--", zorder=1)
    if label_points:
        for _, row in df.iterrows():
            xx = row[f"{dim}_nrc"]
            yy = row[f"{dim}_elicited_mean"]
            dx, dy = 3, 3
            if row["emotion"] in {"happiness", "surprise"}:
                dx = -18
            if row["emotion"] in {"sadness", "calmness"}:
                dy = -9
            ax.annotate(
                JP_LABEL[row["emotion"]],
                (xx, yy),
                xytext=(dx, dy),
                textcoords="offset points",
                fontsize=4.8,
                fontproperties=JP,
            )
    ax.set_xlim(-1.05, 1.05)
    ax.set_ylim(-1.05, 1.05)
    ax.set_xticks([-1, 0, 1])
    ax.set_yticks([-1, 0, 1])
    ax.grid(True, color="#E2E2E2", linewidth=0.45)
    ax.tick_params(labelsize=5.5, length=2)
    ax.set_title(
        f"{title}\nr={r_value:.3f}, Holm p={p_value:.3f}, slope={slope:.3f}",
        fontsize=6.4,
        fontproperties=JP,
        pad=3,
    )
    ax.set_xlabel("意味的評価", fontsize=5.5, fontproperties=JP, labelpad=1)
    ax.set_ylabel("情動体験評価", fontsize=5.5, fontproperties=JP, labelpad=1)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_linewidth(0.6)


def make_va_figure(path: Path) -> None:
    df = noun_data()
    fig, axes = plt.subplots(1, 2)
    add_scatter(axes[0], df, "valence", "感情価 (V)", 0.875, 0.018, 0.520, True)
    add_scatter(axes[1], df, "arousal", "覚醒度 (A)", 0.832, 0.034, 0.341, True)
    fig.subplots_adjust(left=0.10, right=0.99, bottom=0.16, top=0.84, wspace=0.34)
    save_figure(fig, path, 1500, 900)


def make_d_summary_figure(path: Path) -> None:
    df = noun_data()
    fig, axes = plt.subplots(1, 2, gridspec_kw={"width_ratios": [1.04, 0.96]})
    add_scatter(axes[0], df, "dominance", "支配性 (D)", -0.121, 0.792, -0.055, True)

    ax = axes[1]
    dims = ["V", "A", "D"]
    pearson = np.array([0.875, 0.832, -0.121])
    spearman = np.array([0.895, 0.433, -0.417])
    slopes = np.array([0.520, 0.341, -0.055])
    y = np.arange(3)[::-1]
    ax.axvline(0, color="#999999", linewidth=0.7)
    ax.scatter(pearson, y + 0.15, color="#111111", s=18, label="Pearson r")
    ax.scatter(spearman, y - 0.02, color="#666666", marker="s", s=16, label="Spearman ρ")
    ax.scatter(slopes, y - 0.19, color="#2E86C1", marker="^", s=18, label="回帰傾き")
    ax.set_yticks(y)
    ax.set_yticklabels(dims, fontsize=6.5, fontproperties=LATIN)
    ax.set_xlim(-0.55, 1.0)
    ax.set_xticks([-0.5, 0, 0.5, 1.0])
    ax.tick_params(axis="x", labelsize=5.5, length=2)
    ax.grid(axis="x", color="#E2E2E2", linewidth=0.45)
    ax.set_title("次元別の主要指標", fontsize=6.4, fontproperties=JP, pad=3)
    ax.legend(
        loc="lower right",
        fontsize=4.9,
        frameon=False,
        handletextpad=0.4,
        borderaxespad=0.2,
        prop=JP,
    )
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_linewidth(0.6)
    fig.subplots_adjust(left=0.10, right=0.99, bottom=0.15, top=0.84, wspace=0.38)
    save_figure(fig, path, 1500, 900)


TEXT = {
    0: "2026年7月31日",
    1: "感情語に対する意味的評価と映像によって喚起された情動体験とのVAD次元別対応関係の検討",
    2: "電気電子情報工学専攻　　　　　　　　　　　　MA26006  姜 晰頡",
    3: "基盤システム研究　　　　　　　　　　　　　　指導教員　菅谷　みどり",
    4: "背景",
    5: (
        "感情計算では，文章や映像など異なる対象の感情を共通の数値で扱う必要がある．"
        "そこで，感情価（Valence，V），覚醒度（Arousal，A），支配性（Dominance，D）からなるVADモデルが用いられる[1]．"
        "Vは快・不快，Aは活性度，Dは制御感を表す．"
        "同じ軸を用いることで，異なる刺激や計算モデルの結果を比較できる．"
        "そのため，VADは感情語処理，情動認識，刺激選定などに広く利用される．"
    ),
    6: (
        "感情語辞書には，語が一般に表す感情のVAD値が収録される．"
        "一方，映像データセットには，映像によって喚起された情動体験のVAD評定が収録される[2，3]．"
        "両者を同じ座標空間に置けるため，辞書値を映像後の体験値の参照に用いることがある．"
        "しかし，前者の評価対象は語の意味であり，後者は特定状況での体験である[5，6]．"
        "以下，前者を「意味的評価」，後者を「情動体験評価」と呼ぶ．"
        "両者は同じVAD尺度を用いても，測定している対象は同一ではない．"
    ),
    7: (
        "評価対象が異なれば，同じ感情名でも値が一致するとは限らない．"
        "この差を確認せずに辞書値を基準値として使うと，情動体験を誤って表す可能性がある．"
        "辞書値は入手が容易であり，新たな評定実験の負担も小さい．"
        "したがって，利用可能な範囲が分かれば，情動認識モデルの設計を効率化できる．"
        "一方，対応しない次元を使えば，推定結果に系統的な偏りが生じうる．"
        "したがって，両評価がどの次元で，どの程度対応するかを明らかにする必要がある．"
        "これは，VAD値を情動認識や刺激設計に利用する際の妥当性判断に直結する．"
    ),
    8: "先行研究・課題",
    9: (
        "NRC-VADは英語語彙のVAD規範値を収録する[3]．"
        "DREAMERは映像視聴後のVAD評定を収録する[2]．"
        "CASEは映像視聴中の連続VA評定を収録する[4]．"
        "既存研究は各データセットを個別に利用してきた．"
        "しかし，共通する感情カテゴリー名を介し，意味的評価と情動体験評価をV・A・D別に比較した検討は十分でない．"
        "特に，VADを一つのまとまりとして扱うと，次元ごとの差が隠れる．"
        "Vは快・不快，Aは活性度，Dは制御感を表すため，各次元の心理的内容は異なる．"
        "したがって，ある次元で対応しても，他の次元で同じ関係が得られるとは限らない．"
        "また，高い相関は数値的一致を意味しない．"
        "相対方向が同じでも，体験値が中立点付近に集中すれば，辞書値は代替値にならない．"
        "この場合，感情カテゴリーの順序は保たれても，値の振幅は異なる．"
        "相関だけでは，この差を判別できない．"
        "そこで，線形対応，順位対応，値の広がりを分けて調べる必要がある．"
        "さらに，NRC-VADとDREAMERでは参加者，刺激，評定課題が異なる．"
        "よって，本分析で検討できるのはデータセット間のカテゴリー水準の対応である．"
        "個人内の対応や因果関係は検討できない．"
    ),
    10: "目的・提案",
    11: (
        "本研究は，NRC-VADとDREAMERに共通する9感情カテゴリーを対象とする．"
        "目的は，意味的評価と情動体験評価の対応特性をV・A・D別に明らかにすることである．"
        "具体的には，①線形対応，②順位対応，③値の広がりを比較する．"
        "同一性の証明ではなく，辞書値を利用できる範囲と限界を示す．"
        "主要な推論には，V・A・Dを含むDREAMERを用いる．"
        "CASEは，連続VA評定にも同じ処理を適用できるかを確認する補助資料とする．"
    ),
    12: (
        "そのため，共通カテゴリー名を対応づけ，各尺度を[-1，1]に変換する比較枠組みを提案する．"
        "この枠組みでは，「対応」と「数値的一致」を区別する．"
        "線形相関だけでなく，順位相関と回帰傾きも併用する．"
        "これにより，相対構造と値の広がりを別々に評価する．"
        "尺度変換は端点をそろえるための処理であり，測定特性の同一性は仮定しない．"
    ),
    13: "評価（二次データ分析）",
    14: (
        "評価目的は，提案した比較枠組みを9カテゴリーに適用し，次元別の対応を確認することである．"
        "NRC-VADでは感情カテゴリー名の意味的評価を参照した．"
        "DREAMERでは映像視聴後の情動体験評価を用いた．"
        "まず，各尺度の理論上の端点を[-1，1]に変換した．"
        "次に，DREAMERの試行をカテゴリー別に集約した．"
        "最後に，V・A・D別の対応を比較した（図1）．"
        "評価対象をそろえるため，共通する感情カテゴリー名だけを残した．"
        "CASEはVAのみで共通カテゴリーも4つである．"
        "そのため，連続評定への処理手順確認に限定し，主要結論には用いない．"
    ),
    16: "図1．意味的評価と情動体験評価の比較手順",
    17: "比較方法",
    18: "5.1 データと前処理",
    19: (
        "意味的評価にはNRC-VAD v2を用いた[3]．"
        "DREAMERの感情ラベルと同名の英語名詞1語を参照値とした．"
        "これは辞書全体の代表値ではなく，カテゴリーラベル単位の操作化である．"
        "情動体験評価にはDREAMERを用いた[2]．"
        "23名が18映像を評価した414試行を9カテゴリーに集約した．"
        "各カテゴリーは2映像を含む．"
        "各試行のV・A・Dを尺度変換した後，参加者と映像を含むカテゴリー平均を求めた．"
        "この平均を情動体験評価の代表値とした．"
        "語形による影響を確認するため，形容詞への置換も感度分析した．"
        "さらに，DREAMERの支配性尺度の向きを確認した．"
        "符号を反転した場合も分析し，尺度方向の解釈に依存しないかを調べた．"
        "CASEでは30名×8映像の連続VA評定を映像単位に集約した[4]．"
        "ただし，共通カテゴリーが4つしかないため，推論統計には用いなかった．"
    ),
    20: "5.2 統計分析",
    21: (
        "Pearson相関で線形対応を評価した．"
        "Spearman相関で順位対応を評価した．"
        "推論単位が9と少ないため，全9!通りの正確置換検定を行った．"
        "各相関系列のV・A・DはHolm法で補正した．"
        "値の広がりは回帰傾きで近似した．"
        "傾きが1に近ければ，両評価の変化幅が近い．"
        "傾きが1未満ならば，情動体験評価の変化幅が小さい．"
        "ただし，傾きは尺度差そのものではなく，本研究内での近似指標である．"
        "参加者23名と各カテゴリー内の2映像を復元抽出する5,000回の階層bootstrapで95%信頼区間を求めた．"
        "参加者，次いで各カテゴリー内の映像を復元抽出し，両者の差を反映した．"
        "さらに，1カテゴリー除外分析とDの符号反転を行い，判断の頑健性を確認した．"
    ),
    22: "結果",
    23: (
        "VではPearson相関r=.875（Holm p=.018）とSpearman相関ρ=.895（Holm p=.007）がともに支持された．"
        "1カテゴリー除外後のrも.848～.922であった．"
        "AではPearson相関r=.832（Holm p=.034）のみが支持された．"
        "Spearman相関ρ=.433（Holm p=.500）は支持されなかった．"
        "また，calmnessを除くとr=.482まで低下した．"
        "DではPearson相関r=-.121（Holm p=.792）も順位対応も支持されなかった．"
        "Pearson相関の階層bootstrap 95%区間は，Vで[.762，.920]，Aで[.370，.913]，Dで[-.432，.280]であった．"
        "回帰傾きはV=.520，A=.341，D=-.055であった（図2，3）．"
        "VとAの傾きは1未満であるため，高相関でも数値は一致しなかった．"
        "形容詞への置換では主要な判断は変わらなかった．"
        "Dの符号反転でも有意な対応は得られなかった．"
        "CASEにも同じ集約手順を適用できた．"
        "ただし，カテゴリー数が少ないため，DREAMERの結果を再現したとは判断しない．"
    ),
    25: "図2．ValenceとArousalにおける次元別対応",
    27: "図3．Dominanceの対応と次元別主要指標",
    28: "まとめ",
    29: (
        "本研究では，意味的評価と情動体験評価の対応特性がV・A・Dで異なることを示した．"
        "Vは相対構造が比較的安定したが，値の広がりは縮小した．"
        "Aは線形対応に限られ，カテゴリー構成にも敏感であった．"
        "Dでは対応の証拠が得られなかった．"
        "意味的なDは語の一般的な支配感を表す．"
        "一方，体験のDは場面内の主体性や状況統制にも左右されうる[7]．"
        "ただし，本分析はこの機序を直接検証していない．"
        "したがって，Dの非対応を構念差だけで説明することはできない．"
        "刺激構成や評定課題の差も代替説明として残る．"
        "以上から，辞書VADは情動体験評価の代替値ではない．"
        "利用時には次元別の検証と較正が必要である．"
        "対応と数値的一致を分ける比較枠組みを示した点が本研究の貢献である．"
        "この枠組みは，辞書値を情動認識モデルの教師値や刺激基準に用いる前の確認手順として利用できる．"
        "Vは相対方向の参照に限られ，AとDにはVと同じ仮定を適用できない．"
        "ただし，推論単位は9カテゴリーであり，各カテゴリーは名詞1語と2映像に限られる．"
        "参加者と課題もデータセット間で異なる．"
        "したがって，辞書全体，多様な映像，個人内の対応へ一般化できない．"
        "今後は類義語と映像を増やす．"
        "複数の外部データセットでも再検証する．"
        "さらに，同一参加者が語の意味と映像後体験を同一尺度で評価する実験を行う．"
        "その際，語と映像を交差させた混合効果モデルを用いる．"
        "これにより，個人内対応と較正式の一般化可能性を検証する．"
    ),
    30: "参考文献",
    31: (
        '[1] Bradley, M. M., Lang, P. J., J. Behav. Ther. Exp. Psychiatry, 25(1), 49-59, 1994. '
        '[2] Katsigiannis, S., Ramzan, N., IEEE J. Biomed. Health Inform., 22(1), 98-107, 2018.'
    ),
    32: (
        '[3] Mohammad, S. M., "NRC VAD Lexicon v2", arXiv:2503.23547, 2025. '
        '[4] Sharma, K. et al., Sci. Data, 6, 196, 2019.'
    ),
    33: (
        '[5] Barrett, L. F., J. Pers. Soc. Psychol., 87(2), 266-281, 2004. '
        '[6] Robinson, M. D., Clore, G. L., Psychol. Bull., 128(6), 934-960, 2002. '
        '[7] Smith, C. A., Ellsworth, P. C., J. Pers. Soc. Psychol., 48(4), 813-838, 1985.'
    ),
}


def set_paragraph_text(p: etree._Element, text: str) -> None:
    texts = p.xpath(".//w:t", namespaces=NS)
    if texts:
        texts[0].text = text
        if text.startswith(" ") or text.endswith(" "):
            texts[0].set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        for node in texts[1:]:
            node.text = ""
    else:
        r = etree.Element(W + "r")
        t = etree.SubElement(r, W + "t")
        t.text = text
        p.append(r)

    for r in p.xpath(".//w:r", namespaces=NS):
        rpr = r.find(W + "rPr")
        if rpr is None:
            rpr = etree.Element(W + "rPr")
            r.insert(0, rpr)
        rfonts = rpr.find(W + "rFonts")
        if rfonts is None:
            rfonts = etree.Element(W + "rFonts")
            rpr.insert(0, rfonts)
        rfonts.set(W + "ascii", "Times New Roman")
        rfonts.set(W + "hAnsi", "Times New Roman")
        rfonts.set(W + "eastAsia", "Hiragino Mincho ProN")
        rfonts.set(W + "cs", "Times New Roman")
        rfonts.set(W + "hint", "eastAsia")
        lang = rpr.find(W + "lang")
        if lang is None:
            lang = etree.Element(W + "lang")
            rpr.append(lang)
        lang.set(W + "eastAsia", "ja-JP")


def patch_document_xml(data: bytes) -> bytes:
    parser = etree.XMLParser(remove_blank_text=False)
    root = etree.fromstring(data, parser)
    body = root.find(".//w:body", namespaces=NS)
    paragraphs = body.xpath("./w:p", namespaces=NS)
    if len(paragraphs) != 42:
        raise RuntimeError(f"Unexpected template paragraph count: {len(paragraphs)}")

    for idx, text in TEXT.items():
        set_paragraph_text(paragraphs[idx], text)

    for idx in (34, 35, 36, 37, 38, 39, 40, 41):
        body.remove(paragraphs[idx])

    image_names = [
        ("比較手順", "Meaning–experience comparison procedure"),
        ("ValenceとArousalの対応", "Valence and arousal correspondence"),
        ("Dominanceと主要指標", "Dominance correspondence and dimension summary"),
    ]
    for i, node in enumerate(root.xpath(".//wp:docPr", namespaces=NS)):
        if i < len(image_names):
            node.set("name", image_names[i][0])
            node.set("descr", image_names[i][1])
            node.set("title", image_names[i][0])
    for i, node in enumerate(root.xpath(".//pic:cNvPr", namespaces=NS)):
        if i < len(image_names):
            node.set("name", image_names[i][0] + ".png")
            node.set("descr", image_names[i][1])

    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone="yes")


def patch_core_xml(data: bytes) -> bytes:
    parser = etree.XMLParser(remove_blank_text=False)
    root = etree.fromstring(data, parser)
    title = root.find("dc:title", namespaces=NS)
    if title is not None:
        title.text = "感情語と映像誘発情動体験のVAD次元別対応関係"
    subject = root.find("dc:subject", namespaces=NS)
    if subject is not None:
        subject.text = "修士研究概要書"
    creator = root.find("dc:creator", namespaces=NS)
    if creator is not None:
        creator.text = "姜 晰頡"
    modified = root.find("dcterms:modified", namespaces=NS)
    if modified is not None:
        modified.text = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone="yes")


def build_docx() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    flow = FIG_DIR / "image1.png"
    va = FIG_DIR / "image2.png"
    dsum = FIG_DIR / "image3.png"
    make_flow_figure(flow)
    make_va_figure(va)
    make_d_summary_figure(dsum)

    replacements = {
        "word/document.xml": None,
        "docProps/core.xml": None,
        "word/media/image1.png": flow.read_bytes(),
        "word/media/image2.png": va.read_bytes(),
        "word/media/image3.png": dsum.read_bytes(),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    temp_out = OUT.with_suffix(".tmp.docx")
    with zipfile.ZipFile(TEMPLATE, "r") as zin, zipfile.ZipFile(
        temp_out, "w", compression=zipfile.ZIP_DEFLATED
    ) as zout:
        for item in zin.infolist():
            raw = zin.read(item.filename)
            if item.filename == "word/document.xml":
                raw = patch_document_xml(raw)
            elif item.filename == "docProps/core.xml":
                raw = patch_core_xml(raw)
            elif item.filename in replacements and replacements[item.filename] is not None:
                raw = replacements[item.filename]
            zout.writestr(item, raw)
    shutil.move(temp_out, OUT)


if __name__ == "__main__":
    build_docx()
    print(OUT)
