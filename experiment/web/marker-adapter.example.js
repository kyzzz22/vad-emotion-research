/*
Load a reviewed adapter before app.js only after bench-testing the real device.
The hook may be synchronous or return a Promise. Throwing/rejecting records an error.
*/
window.a2MarkerHook = async function a2MarkerHook(record) {
  const numericCode = Number(record.event_code);
  if (!Number.isInteger(numericCode)) {
    throw new Error(`Invalid event code: ${record.event_code}`);
  }

  // Replace this line with exactly one verified device call, for example an
  // LSL outlet push, serial write, or vendor SDK marker function.
  throw new Error(`No device adapter implemented for event ${numericCode}`);
};
