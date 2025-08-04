//FORMATA A DATA VINDA DO SERVIDOR
function formatData(dataText) {
  let fromNowTextCreated = moment.utc(dataText).fromNow();
  return fromNowTextCreated;
}