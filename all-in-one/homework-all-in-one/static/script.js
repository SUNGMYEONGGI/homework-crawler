function appendLog(el, msg){
  const ts = new Date().toLocaleTimeString();
  el.textContent += `[${ts}] ${msg}\n`;
  el.scrollTop = el.scrollHeight;
}

function setProgress(el, ratio){
  const v = Math.max(0, Math.min(1, Number(ratio) || 0));
  el.style.width = `${(v*100).toFixed(1)}%`;
}

// Reminder UI bindings
const r13 = document.getElementById('r-13');
const r14 = document.getElementById('r-14');
const r15 = document.getElementById('r-15');
const r16 = document.getElementById('r-16');
const rStart = document.getElementById('r-start');
const rStop = document.getElementById('r-stop');
const rStatus = document.getElementById('r-status');
const rLogs = document.getElementById('r-logs');
const rProgress = document.getElementById('r-progress');
const rResults = document.getElementById('r-results');
const rChannel = document.getElementById('r-channel');
const rSlackBtn = document.getElementById('r-slack');
const rSlackResp = document.getElementById('r-slack-resp');

// Crawler UI bindings
const cExam = document.getElementById('c-exam');
const cFormat = document.getElementById('c-format');
const cStart = document.getElementById('c-start');
const cStop = document.getElementById('c-stop');
const cStatus = document.getElementById('c-status');
const cLogs = document.getElementById('c-logs');
const cProgress = document.getElementById('c-progress');
const cDownload = document.getElementById('c-download');

// Reminder websocket
let rWs;
function connectReminderWS(){
  rWs = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + '/reminder/ws');
  rWs.onmessage = (e)=>{
    try{
      const data = JSON.parse(e.data);
      if(data.type === 'log') appendLog(rLogs, data.message);
      if(data.type === 'progress') setProgress(rProgress, data.progress);
      if(data.type === 'error') { appendLog(rLogs, 'ERROR: ' + data.message); rStatus.textContent = '오류'; }
      if(data.type === 'complete'){
        appendLog(rLogs, data.message);
        rStatus.textContent = '완료';
        renderReminderResults(data.results);
      }
    }catch(err){ appendLog(rLogs, e.data); }
  };
  rWs.onopen = ()=> appendLog(rLogs, 'WS 연결됨');
  rWs.onclose = ()=> appendLog(rLogs, 'WS 연결 종료');
}
connectReminderWS();

// Crawler websocket
let cWs;
function connectCrawlerWS(){
  cWs = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + '/crawler/ws');
  cWs.onmessage = (e)=>{
    try{
      const data = JSON.parse(e.data);
      if(data.type === 'log') appendLog(cLogs, data.message);
      if(data.type === 'progress') setProgress(cProgress, data.progress);
      if(data.type === 'error') { appendLog(cLogs, 'ERROR: ' + data.message); cStatus.textContent = '오류'; }
      if(data.type === 'complete'){
        appendLog(cLogs, data.message);
        cStatus.textContent = '완료';
        if(data.file_path){
          const a = document.createElement('a');
          a.href = '/crawler/api/download/' + encodeURIComponent(data.file_path);
          a.textContent = '다운로드: ' + data.file_path;
          a.className = 'download-link';
          cDownload.innerHTML = '';
          cDownload.appendChild(a);
        }
      }
    }catch(err){ appendLog(cLogs, e.data); }
  };
  cWs.onopen = ()=> appendLog(cLogs, 'WS 연결됨');
  cWs.onclose = ()=> appendLog(cLogs, 'WS 연결 종료');
}
connectCrawlerWS();

function renderReminderResults(results){
  if(!results){ rResults.textContent = '결과 없음'; return; }
  const non = results.non_submitted_by_cohort || {};
  const lines = [];
  for(const cohort of Object.keys(non).sort()){
    const names = non[cohort] || [];
    lines.push(`${cohort}기 미제출(${names.length}) : ${names.slice(0, 20).join(', ')}${names.length>20?' ...':''}`);
  }
  rResults.textContent = lines.join('\n');
}

// Actions: Reminder
rStart.disabled = true; rStop.disabled = true; rSlackBtn.disabled = true;
cStart.disabled = true; cStop.disabled = true;

// Availability check
(async function initAvailability(){
  try{
    const res = await fetch('/api/availability');
    const a = await res.json();
    if(a.reminder){ rStart.disabled = false; rStop.disabled = false; }
    if(a.reminder_slack){ rSlackBtn.disabled = false; }
    if(a.crawler){ cStart.disabled = false; cStop.disabled = false; }
    if(!a.reminder) appendLog(rLogs, '리마인더 모듈 없음: UI 비활성화');
    if(!a.reminder_slack) appendLog(rLogs, '슬랙 기능 없음: 전송 버튼 비활성화');
    if(!a.crawler) appendLog(cLogs, '크롤러 모듈 없음: UI 비활성화');
  }catch(err){ appendLog(rLogs, '가용성 확인 실패: ' + err); }
})();

rStart.onclick = async ()=>{
  rStatus.textContent = '실행 중';
  setProgress(rProgress, 0);
  rLogs.textContent = '';
  rSlackResp.textContent = '';
  const payload = {
    cohort_13: r13.value.trim(),
    cohort_14: r14.value.trim(),
    cohort_15: r15.value.trim(),
    cohort_16: r16.value.trim(),
  };
  const res = await fetch('/reminder/api/check_homework', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
  const data = await res.json();
  if(!res.ok){ appendLog(rLogs, '요청 실패: ' + (data.detail || JSON.stringify(data))); rStatus.textContent = '대기'; }
  else{ appendLog(rLogs, data.message || '시작됨'); }
};

rStop.onclick = async ()=>{
  const res = await fetch('/reminder/api/stop', {method:'POST'});
  const data = await res.json();
  appendLog(rLogs, data.message || '중지 요청');
};

rSlackBtn.onclick = async ()=>{
  // 최신 결과를 서버에서 가져와 non_submitted_by_cohort 사용
  const res = await fetch('/reminder/api/results');
  const results = await res.json();
  if(!results || !results.non_submitted_by_cohort){
    rSlackResp.textContent = '보낼 데이터가 없습니다.';
    return;
  }
  const payload = {
    cohort_exam_ids: results.cohort_exam_ids || {},
    non_submitted_by_cohort: results.non_submitted_by_cohort,
    channel: (rChannel.value || '').trim() || null,
  };
  const res2 = await fetch('/reminder/api/send_slack_reminder', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
  const data2 = await res2.json();
  rSlackResp.textContent = data2.message || JSON.stringify(data2);
};

// Actions: Crawler
cStart.onclick = async ()=>{
  cStatus.textContent = '실행 중';
  setProgress(cProgress, 0);
  cLogs.textContent = '';
  cDownload.innerHTML = '';
  const payload = { exam_id: (cExam.value || '').trim(), file_format: cFormat.value };
  const res = await fetch('/crawler/api/crawl', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
  const data = await res.json();
  if(!res.ok){ appendLog(cLogs, '요청 실패: ' + (data.detail || JSON.stringify(data))); cStatus.textContent = '대기'; }
  else{ appendLog(cLogs, data.message || '시작됨'); }
};

cStop.onclick = async ()=>{
  const res = await fetch('/crawler/api/stop', {method:'POST'});
  const data = await res.json();
  appendLog(cLogs, data.message || '중지 요청');
};


