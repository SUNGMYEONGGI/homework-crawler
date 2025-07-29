// FastCampus LMS Crawler Frontend JavaScript
class CrawlerApp {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.isCrawling = false;
        this.currentFilePath = null;
        
        this.initializeElements();
        this.bindEvents();
        this.connectWebSocket();
        this.updateStatus('대기중');
    }

    initializeElements() {
        // 폼 요소들
        this.examIdInput = document.getElementById('exam-id');
        this.fileFormatSelect = document.getElementById('file-format');
        this.startBtn = document.getElementById('start-btn');
        this.stopBtn = document.getElementById('stop-btn');
        
        // 진행상황 요소들
        this.progressFill = document.getElementById('progress-fill');
        this.progressText = document.getElementById('progress-text');
        this.progressDesc = document.getElementById('progress-desc');
        
        // 통계 요소들
        this.collectedCountEl = document.getElementById('collected-count');
        this.examIdDisplayEl = document.getElementById('exam-id-display');
        this.fileFormatDisplayEl = document.getElementById('file-format-display');
        
        // 로그 요소들
        this.logContent = document.getElementById('log-content');
        this.clearLogBtn = document.getElementById('clear-log-btn');
        
        // 결과 요소들
        this.resultContainer = document.getElementById('result-container');
        this.downloadMessage = document.getElementById('download-message');
        this.downloadBtn = document.getElementById('download-btn');
        
        // 상태 표시기
        this.statusIndicator = document.getElementById('status-indicator');
        
        // 토스트 컨테이너
        this.toastContainer = document.getElementById('toast-container');
    }

    bindEvents() {
        // 시작 버튼
        this.startBtn.addEventListener('click', () => this.startCrawling());
        
        // 중지 버튼
        this.stopBtn.addEventListener('click', () => this.stopCrawling());
        
        // 로그 지우기 버튼
        this.clearLogBtn.addEventListener('click', () => this.clearLog());
        
        // 다운로드 버튼
        this.downloadBtn.addEventListener('click', () => this.downloadFile());
        
        // Enter 키로 시작
        this.examIdInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !this.isCrawling) {
                this.startCrawling();
            }
        });
        
        // 입력값 변경 시 통계 업데이트
        this.examIdInput.addEventListener('input', () => this.updateStats());
        this.fileFormatSelect.addEventListener('change', () => this.updateStats());
    }

    connectWebSocket() {
        const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${location.host}/ws`;
        
        this.socket = new WebSocket(wsUrl);
        
        this.socket.onopen = () => {
            this.isConnected = true;
            this.addLog('WebSocket 연결됨', 'success');
            this.updateStatus('연결됨', 'active');
        };
        
        this.socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            } catch (error) {
                console.error('WebSocket 메시지 파싱 오류:', error);
            }
        };
        
        this.socket.onclose = () => {
            this.isConnected = false;
            this.updateStatus('연결 끊김', 'error');
            this.addLog('WebSocket 연결이 끊어졌습니다. 재연결 시도 중...', 'warning');
            
            // 5초 후 재연결 시도
            setTimeout(() => {
                if (!this.isConnected) {
                    this.connectWebSocket();
                }
            }, 5000);
        };
        
        this.socket.onerror = (error) => {
            console.error('WebSocket 오류:', error);
            this.addLog('WebSocket 연결 오류가 발생했습니다.', 'error');
        };
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'log':
                this.addLog(data.message, 'info');
                break;
                
            case 'progress':
                this.updateProgress(data.progress, data.description);
                break;
                
            case 'complete':
                this.handleCrawlingComplete(data);
                break;
                
            case 'error':
                this.handleCrawlingError(data.message);
                break;
                
            case 'info':
                this.addLog(data.message, 'info');
                this.showToast(data.message, 'info');
                break;
                
            default:
                console.log('알 수 없는 메시지 타입:', data);
        }
    }

    async startCrawling() {
        const examId = this.examIdInput.value.trim();
        const fileFormat = this.fileFormatSelect.value;
        
        if (!examId) {
            this.showToast('시험 ID를 입력해주세요.', 'warning');
            this.examIdInput.focus();
            return;
        }
        
        if (!/^\d+$/.test(examId)) {
            this.showToast('시험 ID는 숫자만 입력 가능합니다.', 'error');
            this.examIdInput.focus();
            return;
        }
        
        this.isCrawling = true;
        this.updateButtonStates();
        this.hideResultContainer();
        this.resetProgress();
        this.updateStats();
        this.updateStatus('크롤링 중', 'active');
        
        try {
            const response = await fetch('/api/crawl', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    exam_id: examId,
                    file_format: fileFormat
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || '크롤링 시작 실패');
            }
            
            const result = await response.json();
            this.addLog(`크롤링이 시작되었습니다. (시험 ID: ${result.exam_id})`, 'success');
            this.showToast('크롤링이 시작되었습니다!', 'success');
            
        } catch (error) {
            this.handleCrawlingError(error.message);
        }
    }

    async stopCrawling() {
        try {
            const response = await fetch('/api/stop', {
                method: 'POST'
            });
            
            if (response.ok) {
                const result = await response.json();
                this.addLog(result.message, 'warning');
                this.showToast('크롤링이 중지되었습니다.', 'warning');
            }
        } catch (error) {
            this.addLog(`중지 요청 실패: ${error.message}`, 'error');
            this.showToast('중지 요청이 실패했습니다.', 'error');
        }
        
        this.isCrawling = false;
        this.updateButtonStates();
        this.updateStatus('중지됨', 'error');
    }

    handleCrawlingComplete(data) {
        this.isCrawling = false;
        this.updateButtonStates();
        this.updateStatus('완료', 'success');
        
        this.currentFilePath = data.file_path;
        this.updateCollectedCount(data.count);
        
        this.addLog(data.message, 'success');
        this.showToast(`크롤링 완료! ${data.count}개 데이터 수집됨`, 'success');
        
        if (data.file_path) {
            this.showResultContainer(data.file_path, data.count);
        }
        
        this.updateProgress(1, '작업 완료');
    }

    handleCrawlingError(message) {
        this.isCrawling = false;
        this.updateButtonStates();
        this.updateStatus('오류', 'error');
        
        this.addLog(message, 'error');
        this.showToast(message, 'error');
    }

    updateProgress(progress, description) {
        const percentage = Math.round(progress * 100);
        this.progressFill.style.width = `${percentage}%`;
        this.progressText.textContent = `${percentage}%`;
        this.progressDesc.textContent = description || '진행 중...';
        
        // 진행률에 따른 색상 변화
        if (percentage === 100) {
            this.progressFill.style.background = 'linear-gradient(90deg, var(--success-500), var(--accent-500))';
        } else {
            this.progressFill.style.background = 'linear-gradient(90deg, var(--primary-500), var(--accent-500))';
        }
    }

    resetProgress() {
        this.updateProgress(0, '대기 중...');
        this.updateCollectedCount(0);
    }

    updateCollectedCount(count) {
        this.collectedCountEl.textContent = count;
        
        // 카운트 애니메이션
        this.collectedCountEl.style.transform = 'scale(1.2)';
        this.collectedCountEl.style.color = 'var(--success-500)';
        
        setTimeout(() => {
            this.collectedCountEl.style.transform = 'scale(1)';
            this.collectedCountEl.style.color = 'var(--text-primary)';
        }, 300);
    }

    updateStats() {
        const examId = this.examIdInput.value.trim() || '-';
        const fileFormat = this.fileFormatSelect.value.toUpperCase() || '-';
        
        this.examIdDisplayEl.textContent = examId;
        this.fileFormatDisplayEl.textContent = fileFormat;
    }

    updateButtonStates() {
        this.startBtn.disabled = this.isCrawling;
        this.stopBtn.disabled = !this.isCrawling;
        this.examIdInput.disabled = this.isCrawling;
        this.fileFormatSelect.disabled = this.isCrawling;
        
        if (this.isCrawling) {
            this.startBtn.classList.add('loading');
        } else {
            this.startBtn.classList.remove('loading');
        }
    }

    updateStatus(text, type = '') {
        const statusText = this.statusIndicator.querySelector('span');
        statusText.textContent = text;
        
        // 상태 클래스 제거
        this.statusIndicator.classList.remove('active', 'error');
        
        // 새 상태 클래스 추가
        if (type) {
            this.statusIndicator.classList.add(type);
        }
    }

    addLog(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString('ko-KR');
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${type}`;
        
        logEntry.innerHTML = `
            <span class="log-time">[${timestamp}]</span>
            <span class="log-message">${this.escapeHtml(message)}</span>
        `;
        
        this.logContent.appendChild(logEntry);
        this.logContent.scrollTop = this.logContent.scrollHeight;
        
        // 로그 항목이 너무 많으면 오래된 것 제거
        const logEntries = this.logContent.querySelectorAll('.log-entry');
        if (logEntries.length > 100) {
            logEntries[0].remove();
        }
    }

    clearLog() {
        this.logContent.innerHTML = `
            <div class="log-entry info">
                <span class="log-time">[시스템]</span>
                <span class="log-message">로그가 지워졌습니다.</span>
            </div>
        `;
        this.showToast('로그가 지워졌습니다.', 'info');
    }

    showResultContainer(filePath, count) {
        this.downloadMessage.textContent = `${count}개의 데이터가 수집되어 파일이 준비되었습니다!`;
        this.resultContainer.style.display = 'block';
        
        // 스크롤 애니메이션
        this.resultContainer.scrollIntoView({ behavior: 'smooth' });
    }

    hideResultContainer() {
        this.resultContainer.style.display = 'none';
    }

    downloadFile() {
        if (this.currentFilePath) {
            const link = document.createElement('a');
            link.href = `/api/download/${encodeURIComponent(this.currentFilePath)}`;
            link.download = this.currentFilePath;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            this.showToast('파일 다운로드가 시작됩니다.', 'success');
        } else {
            this.showToast('다운로드할 파일이 없습니다.', 'error');
        }
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        
        toast.innerHTML = `
            <div class="toast-content">
                <i class="toast-icon ${icons[type] || icons.info}"></i>
                <span class="toast-message">${this.escapeHtml(message)}</span>
                <button class="toast-close">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        this.toastContainer.appendChild(toast);
        
        // 닫기 버튼 이벤트
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => {
            this.removeToast(toast);
        });
        
        // 자동 제거 (5초 후)
        setTimeout(() => {
            this.removeToast(toast);
        }, 5000);
    }

    removeToast(toast) {
        if (toast && toast.parentNode) {
            toast.style.animation = 'slideOutRight 0.3s ease-out';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// 애플리케이션 초기화
document.addEventListener('DOMContentLoaded', () => {
    window.crawlerApp = new CrawlerApp();
});

// 추가 CSS 애니메이션을 위한 동적 스타일
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOutRight {
        from {
            opacity: 1;
            transform: translateX(0);
        }
        to {
            opacity: 0;
            transform: translateX(100%);
        }
    }
`;
document.head.appendChild(style); 