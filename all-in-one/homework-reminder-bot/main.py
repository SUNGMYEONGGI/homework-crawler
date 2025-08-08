from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import asyncio

class HomeworkReminderBot:
    def __init__(self):
        self.email = "help.edu@fastcampus.co.kr"
        self.password = "Camp1017!!"
        self.driver = None
        self.wait = None
        self.log_messages = []
        self.submitted_students = []  # 제출한 학생 리스트
        
        # 전체 수강생 리스트
        self.students_13 = [
            "강연경", "고민주", "김두환", "김문수", "김재덕", "김재훈", "김정빈", "김주형",
            "김태현", "김효석", "나주영", "류지헌", "문국현", "문진숙", "박성진", "박진섭",
            "소재목", "송규헌", "신광영", "염창환", "오승태", "이경도", "이나경", "이상원",
            "이상현", "이승민", "이승현", "이영준", "이재용", "이정민", "이준석", "이진식",
            "정재훈", "조선미", "조은별", "조의영", "조재형", "진정", "채병기", "최웅비",
            "최지희", "편아현", "홍상호", "홍정민"
        ]
        
        self.students_14 = [
            "김광묵", "김동준", "김명철", "김병현", "김상윤", "김선민", "김수환", "김승완", 
            "김시진", "김영", "김장원", "문채린", "민병호", "박재홍", "백의진", "송인섭", 
            "신준엽", "안희원", "오창조", "이가은", "이건희", "이윤서", "이준영", "이찬", 
            "임예슬", "장윤정", "전수정", "정민지", "정서우", "정소현", "정예은", "최현화"
        ]
        
        self.students_15 = [
            "권중우", "김민규", "김민수", "김병진", "김여정", "김정은", "김종국", "김지은", 
            "김태리", "김태훈", "박근민", "박용환", "박지환", "박지희", "배진환", "백지연", 
            "손윤희", "신대식", "신세훈", "신지현", "오준혁", "윤새난슬", "윤태영", "이승규", 
            "이유정", "이은총", "이창묵", "이현승", "이현우", "임태훈", "임한철", "전태호", 
            "전해영", "차선경", "천대웅", "최상일", "최장혁", "최지희", "하성창", "한성현", 
            "한주희", "함주희"
        ]
        
        self.students_16 = [
            "고민서", "권문진", "권효주", "김동근", "김소은", "김수현", "김예인", 
            "김재록", "김종범", "김종화", "김진우", "김하은", "문서연", "박준수", 
            "박준영", "손은혜", "안현태", "오정택", "원정연", "유영호", "윤소영", 
            "이동건", "이수민", "이승호", "이재윤", "임환석", "정무곤", "정용재", 
            "주예령", "최보경", "최해혁", "최현", "허예경", "황은혜", "황준승"
        ]
        
    def _add_log(self, message):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.log_messages.append(log_entry)
        print(log_entry)



    def setup_driver(self):
        self._add_log("Selenium 드라이버 설정 시작...")
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # 🔥 헤드리스 모드 다시 활성화 (안정성)
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-extensions")
        # 🔥 macOS 안정성을 위한 추가 옵션
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--disable-field-trial-config")
        chrome_options.add_argument("--disable-ipc-flooding-protection")
        chrome_options.add_argument("--remote-debugging-port=9222")  # 디버깅 포트
        chrome_options.add_experimental_option("prefs", {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "autofill.profile_enabled": False
        })
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        try:
            # 🔥 Mac ARM64 호환성을 위해 Homebrew 경로 우선 사용
            chromedriver_path = self._find_chromedriver_path()
            
            if chromedriver_path:
                service = Service(chromedriver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.wait = WebDriverWait(self.driver, 20)
                self._add_log(f"Selenium 드라이버 설정 완료: {chromedriver_path}")
            else:
                raise Exception("ChromeDriver를 찾거나 설치할 수 없습니다.")
                
        except Exception as e:
            self._add_log(f"드라이버 설정 실패: {e}")
            self._add_log("해결 방법: 터미널에서 'brew install chromedriver' 명령어를 실행해주세요.")
            raise
    
    def _find_chromedriver_path(self):
        """ChromeDriver 경로를 찾거나 설치"""
        import subprocess
        import os
        
        # 1. Homebrew로 설치된 chromedriver 찾기 (우선순위)
        homebrew_paths = [
            '/opt/homebrew/bin/chromedriver',  # Apple Silicon Mac
            '/usr/local/bin/chromedriver'      # Intel Mac
        ]
        
        for path in homebrew_paths:
            if os.path.exists(path):
                self._add_log(f"Homebrew ChromeDriver 발견: {path}")
                return path
        
        # 2. PATH에서 chromedriver 찾기
        try:
            result = subprocess.run(['which', 'chromedriver'], capture_output=True, text=True)
            if result.returncode == 0:
                path = result.stdout.strip()
                self._add_log(f"PATH에서 ChromeDriver 발견: {path}")
                return path
        except:
            pass
        
        # 3. ChromeDriver 자동 설치 시도 (Homebrew 사용)
        self._add_log("ChromeDriver를 찾을 수 없습니다. Homebrew로 설치를 시도합니다...")
        try:
            # Homebrew 설치 확인
            subprocess.run(['brew', '--version'], capture_output=True, check=True)
            self._add_log("Homebrew 발견. ChromeDriver 설치 중...")
            
            # ChromeDriver 설치
            subprocess.run(['brew', 'install', 'chromedriver'], capture_output=True, check=True)
            
            # 재검색
            for path in homebrew_paths:
                if os.path.exists(path):
                    self._add_log(f"ChromeDriver 설치 완료: {path}")
                    return path
        except subprocess.CalledProcessError:
            self._add_log("Homebrew를 통한 ChromeDriver 설치 실패")
        except FileNotFoundError:
            self._add_log("Homebrew가 설치되지 않았습니다.")
        
        # 4. 마지막 수단: webdriver-manager 사용 (문제가 있을 수 있음)
        try:
            self._add_log("마지막 수단으로 webdriver-manager 시도...")
            from webdriver_manager.chrome import ChromeDriverManager
            path = ChromeDriverManager().install()
            # 실제 chromedriver 파일인지 확인
            if path and os.path.basename(path) == 'chromedriver':
                self._add_log(f"webdriver-manager로 ChromeDriver 설치: {path}")
                return path
        except Exception as e:
            self._add_log(f"webdriver-manager 실패: {e}")
        
        return None

    def login_process(self):
        self._add_log("🚀 로그인 프로세스 시작...")
        if self.driver:
            try: 
                self.driver.quit()
                self._add_log("기존 드라이버 종료.")
            except: 
                pass
        
        self._add_log("🌐 Chrome 브라우저 설정 중...")
        self.setup_driver()
        
        try:
            self._add_log("📄 로그인 페이지로 이동...")
            self.driver.get("https://lmsadmin-kdt.fastcampus.co.kr/sign-in")
            self._add_log(f"현재 페이지 URL: {self.driver.current_url}")
            
            self._add_log("🏢 사이트 선택 드롭다운 찾는 중...")
            site_select = self.wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="site"]')))
            Select(site_select).select_by_index(0)
            self._add_log("✅ 사이트 선택 완료.")
            time.sleep(0.2)
            
            self._add_log("📧 이메일 입력 필드 찾는 중...")
            email_input = self.wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="userName"]')))
            email_input.clear()
            email_input.send_keys(self.email)
            self._add_log(f"✅ 이메일 입력 완료: {self.email}")
            
            self._add_log("🔐 비밀번호 입력 필드 찾는 중...")
            password_input = self.wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="password"]')))
            password_input.clear()
            password_input.send_keys(self.password)
            self._add_log("✅ 비밀번호 입력 완료.")
            
            self._add_log("🔘 로그인 버튼 찾는 중...")
            login_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/main/section/div/form/button')))
            self.driver.execute_script("arguments[0].click();", login_button)
            self._add_log("✅ 로그인 버튼 클릭 완료.")
            
            self._add_log("⏳ 로그인 처리 대기 중...")
            self.wait.until(lambda drv: drv.current_url != "https://lmsadmin-kdt.fastcampus.co.kr/sign-in")
            self._add_log(f"✅ 로그인 성공! 현재 URL: {self.driver.current_url}")
            
            current_url = self.driver.current_url
            self._add_log("🆕 새 탭 생성 중...")
            self.driver.execute_script("window.open('', '_blank');")
            time.sleep(0.2)
            
            if len(self.driver.window_handles) > 1:
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[-1])
                self._add_log("🔄 새 탭으로 전환 완료.")
            
            self.driver.get(current_url)
            self._add_log(f"✅ 새 탭에서 URL ({current_url})로 이동 완료.")
            time.sleep(1)
            return True
            
        except Exception as e:
            self._add_log(f"❌ 로그인 실패: {str(e)}")
            self._add_log(f"현재 URL: {self.driver.current_url if self.driver else 'N/A'}")
            if self.driver:
                self.driver.quit()
            self.driver = None
            raise

    def navigate_to_exam_management(self):
        """학습관리 > 시험관리로 이동"""
        try:
            self._add_log(f"📍 현재 페이지: {self.driver.current_url}")
            self._add_log("🎯 학습관리 버튼 찾는 중...")
            # 학습관리 버튼 클릭
            learning_management_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/nav/ul[1]/div'))
            )
            self.driver.execute_script("arguments[0].click();", learning_management_button)
            self._add_log("✅ 학습관리 버튼 클릭 완료.")
            time.sleep(1)
            
            self._add_log("📋 시험관리 하위 메뉴 찾는 중...")
            # 시험관리 버튼 클릭
            exam_management_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/nav/ul[1]/div[2]/li[1]'))
            )
            self.driver.execute_script("arguments[0].click();", exam_management_button)
            self._add_log("✅ 시험관리 버튼 클릭 완료.")
            self._add_log(f"📍 이동 후 페이지: {self.driver.current_url}")
            time.sleep(2)
            
            return True
        except Exception as e:
            self._add_log(f"❌ 시험관리 이동 실패: {str(e)}")
            self._add_log(f"📍 실패 시점 URL: {self.driver.current_url}")
            return False

    def navigate_to_exam_detail(self, exam_id):
        """특정 시험 상세 페이지로 이동"""
        try:
            target_url = f"https://lmsadmin-kdt.fastcampus.co.kr/exams/{exam_id}/detail"
            self._add_log(f"🎯 시험 상세 페이지로 이동: {target_url}")
            self._add_log(f"📍 이동 전 현재 URL: {self.driver.current_url}")
            
            self.driver.get(target_url)
            self._add_log("⏳ 페이지 로딩 대기 중...")
            time.sleep(2)
            
            # 페이지 로드 확인
            self._add_log("🔍 메인 섹션 요소 찾는 중...")
            main_section = self.wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="app"]/main/section')))
            self._add_log("✅ 시험 상세 페이지 로드 완료.")
            self._add_log(f"📍 최종 도착 URL: {self.driver.current_url}")
            return True
            
        except Exception as e:
            self._add_log(f"❌ 시험 상세 페이지 이동 실패: {str(e)}")
            self._add_log(f"📍 실패 시점 URL: {self.driver.current_url if self.driver else 'N/A'}")
            return False

    def collect_submitted_students(self, progress_callback=None):
        """제출한 학생들의 이름을 수집"""
        self.submitted_students = []
        
        try:
            # 전체 학생 수 확인
            total_count = 0
            try:
                pagination_element = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="app"]/main/section/div/div[2]/div/div[2]/div[2]/span[2]'))
                )
                pagination_text = pagination_element.text.strip()
                if '/' in pagination_text:
                    total_count = int(pagination_text.split('/')[1].strip())
                else:
                    total_count = int(pagination_text)
                
                self._add_log(f"총 {total_count}명의 학생 확인.")
                if progress_callback:
                    progress_callback(40, f"총 {total_count}명의 학생 확인 완료", self.submitted_students.copy(), total_count)
            except Exception as e:
                self._add_log(f"페이지네이션 확인 실패: {e}")
                total_count = 1
                if progress_callback:
                    progress_callback(40, f"페이지네이션 확인 실패, 단일 항목 처리", self.submitted_students.copy(), 1)
            
            # 각 학생 정보 수집
            for i in range(total_count):
                try:
                    # 진행률 계산 (40%~90% 범위)
                    progress_percent = 40 + (i / total_count) * 50
                    
                    # 학생 이름 수집
                    student_name_element = self.wait.until(
                        EC.visibility_of_element_located((By.XPATH, '//*[@id="app"]/main/section/div/div[2]/div/div[2]/div[1]/strong'))
                    )
                    student_name = student_name_element.text.strip()
                    
                    if student_name and student_name not in self.submitted_students:
                        self.submitted_students.append(student_name)
                        self._add_log(f"제출 학생 수집: {student_name} ({i+1}/{total_count})")
                        
                        # 진행상황 콜백 호출
                        if progress_callback:
                            message = f"📝 {student_name} 수집 완료 ({i+1}/{total_count})"
                            progress_callback(progress_percent, message, self.submitted_students.copy(), total_count)
                    
                    # 다음 학생으로 이동 (마지막이 아닌 경우)
                    if i < total_count - 1:
                        if progress_callback:
                            progress_callback(progress_percent, f"다음 학생으로 이동 중... ({i+2}/{total_count})", self.submitted_students.copy(), total_count)
                        
                        next_button = self.wait.until(
                            EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/main/section/div/div[2]/div/div[2]/div[2]/button[2]'))
                        )
                        self.driver.execute_script("arguments[0].click();", next_button)
                        time.sleep(1)
                        
                except Exception as e:
                    self._add_log(f"{i+1}번째 학생 처리 중 오류: {e}")
                    if progress_callback:
                        progress_callback(progress_percent, f"❌ {i+1}번째 학생 처리 중 오류 발생", self.submitted_students.copy(), total_count)
                    
                    # 오류가 발생해도 다음 학생으로 이동 시도
                    if i < total_count - 1:
                        try:
                            next_button = self.driver.find_element(By.XPATH, '//*[@id="app"]/main/section/div/div[2]/div/div[2]/div[2]/button[2]')
                            if next_button.is_enabled():
                                self.driver.execute_script("arguments[0].click();", next_button)
                                time.sleep(1)
                            else:
                                break
                        except:
                            break
                    continue
            
            self._add_log(f"제출 학생 수집 완료. 총 {len(self.submitted_students)}명")
            if progress_callback:
                progress_callback(90, f"✅ 제출 학생 수집 완료! 총 {len(self.submitted_students)}명", self.submitted_students.copy(), total_count)
            
            return self.submitted_students
            
        except Exception as e:
            self._add_log(f"학생 정보 수집 중 오류: {e}")
            if progress_callback:
                progress_callback(0, f"❌ 학생 정보 수집 중 오류: {str(e)}", self.submitted_students.copy(), 0)
            return self.submitted_students

    def get_non_submitted_students_by_cohort(self, cohort_exam_ids):
        """기수별 미제출 학생 리스트 반환"""
        cohorts = {
            '13': self.students_13,
            '14': self.students_14,
            '15': self.students_15,
            '16': self.students_16
        }
        
        non_submitted_by_cohort = {}
        
        for cohort, exam_id in cohort_exam_ids.items():
            if not exam_id:  # 비어있는 기수는 건너뜀
                continue
                
            cohort_students = cohorts.get(cohort, [])
            non_submitted = []
            
            for student in cohort_students:
                if student not in self.submitted_students:
                    non_submitted.append(student)
            
            non_submitted_by_cohort[cohort] = non_submitted
            self._add_log(f"{cohort}기 미제출 학생 {len(non_submitted)}명 확인:")
            for student in non_submitted:
                self._add_log(f"  - {student}")
                
        return non_submitted_by_cohort

    def run_homework_check_multiple(self, cohort_exam_ids, progress_callback=None):
        """기수별 여러 과제 확인 프로세스 실행"""
        try:
            # 비어있지 않은 시험 ID들만 필터링
            valid_exams = {cohort: exam_id for cohort, exam_id in cohort_exam_ids.items() if exam_id and exam_id.strip()}
            
            if not valid_exams:
                self._add_log("확인할 시험 ID가 없습니다.")
                return False
            
            total_exams = len(valid_exams)
            self._add_log(f"총 {total_exams}개 시험 확인 시작: {list(valid_exams.values())}")
            
            # 1. 로그인
            if progress_callback:
                progress_callback(5, "🔐 로그인 진행 중...", [], 0)
            if not self.login_process():
                return False
            
            # 2. 시험관리 페이지로 이동
            if progress_callback:
                progress_callback(10, "📚 시험관리 페이지로 이동 중...", [], 0)
            if not self.navigate_to_exam_management():
                return False
            
            # 기수별 결과를 저장할 딕셔너리들
            cohort_results = {}
            all_submitted_students = []
            exam_count = 0
            
            # 3. 각 시험별로 순차 처리 (독립적으로)
            for cohort, exam_id in valid_exams.items():
                exam_count += 1
                base_progress = 15 + (exam_count - 1) * 70 / total_exams
                
                self._add_log(f"\n🎯 {cohort}기 시험 ID {exam_id} 처리 시작 ({exam_count}/{total_exams})")
                if progress_callback:
                    progress_callback(base_progress, f"📋 {cohort}기 시험 ID {exam_id} 처리 중... ({exam_count}/{total_exams})", all_submitted_students.copy(), len(all_submitted_students))
                
                # 시험 상세 페이지로 이동
                if not self.navigate_to_exam_detail(exam_id):
                    self._add_log(f"❌ {cohort}기 시험 ID {exam_id} 페이지 이동 실패, 건너뜀")
                    cohort_results[cohort] = {
                        'exam_id': exam_id,
                        'submitted': [],
                        'non_submitted': getattr(self, f'students_{cohort}'),
                        'error': '페이지 이동 실패'
                    }
                    continue
                
                # 제출 학생 정보 수집 (기수별로 독립적으로)
                if progress_callback:
                    progress_callback(base_progress + 10, f"👥 {cohort}기 제출 학생 정보 수집 중...", all_submitted_students.copy(), len(all_submitted_students))
                
                # 각 기수별로 독립적으로 제출 학생 수집
                cohort_submitted = self.collect_submitted_students(
                    lambda progress, message, students, total: progress_callback and progress_callback(
                        base_progress + 10 + progress/100 * 50, 
                        f"{cohort}기: {message}", 
                        all_submitted_students.copy(), 
                        len(all_submitted_students)
                    ) if progress_callback else None
                )
                
                # 해당 기수 학생들과 비교하여 미제출자 확인
                cohort_students = getattr(self, f'students_{cohort}')
                cohort_non_submitted = [student for student in cohort_students if student not in cohort_submitted]
                
                # 기수별 결과 저장
                cohort_results[cohort] = {
                    'exam_id': exam_id,
                    'submitted': cohort_submitted.copy(),
                    'non_submitted': cohort_non_submitted.copy()
                }
                
                # 전체 제출 학생 리스트에 추가 (중복 제거)
                for student in cohort_submitted:
                    if student not in all_submitted_students:
                        all_submitted_students.append(student)
                
                self._add_log(f"✅ {cohort}기 결과: 제출 {len(cohort_submitted)}명, 미제출 {len(cohort_non_submitted)}명")
                self._add_log(f"   📝 {cohort}기 제출한 학생: {', '.join(cohort_submitted[:10])}{' ...' if len(cohort_submitted) > 10 else ''}")
                self._add_log(f"   ❌ {cohort}기 미제출 학생: {', '.join(cohort_non_submitted[:10])}{' ...' if len(cohort_non_submitted) > 10 else ''}")
                
                if progress_callback:
                    progress_callback(base_progress + 60, f"✅ {cohort}기 완료: 제출 {len(cohort_submitted)}명, 미제출 {len(cohort_non_submitted)}명", all_submitted_students.copy(), len(all_submitted_students))
            
            # 4. 최종 결과 정리
            if progress_callback:
                progress_callback(90, "📊 최종 결과 정리 중...", all_submitted_students.copy(), len(all_submitted_students))
            
            # 기수별 미제출 학생 딕셔너리 생성
            non_submitted_by_cohort = {}
            for cohort, result in cohort_results.items():
                if 'non_submitted' in result:
                    non_submitted_by_cohort[cohort] = result['non_submitted']
            
            # 전체 통계 계산
            total_students = sum(len(getattr(self, f'students_{cohort}')) for cohort in valid_exams.keys())
            total_non_submitted = sum(len(students) for students in non_submitted_by_cohort.values())
            
            self._add_log(f"\n🎉 전체 완료!")
            self._add_log(f"   📊 전체 대상 학생: {total_students}명")
            self._add_log(f"   ✅ 전체 제출: {len(all_submitted_students)}명")
            self._add_log(f"   ❌ 전체 미제출: {total_non_submitted}명")
            
            if progress_callback:
                progress_callback(100, f"✅ 완료! 제출: {len(all_submitted_students)}명, 미제출: {total_non_submitted}명", all_submitted_students.copy(), len(all_submitted_students))
            
            return {
                'cohort_exam_ids': cohort_exam_ids,
                'cohort_results': cohort_results,
                'submitted': all_submitted_students,
                'non_submitted_by_cohort': non_submitted_by_cohort,
                'total_students': total_students,
                'submitted_count': len(all_submitted_students),
                'non_submitted_count': total_non_submitted
            }
            
        except Exception as e:
            self._add_log(f"과제 확인 프로세스 실행 중 오류: {e}")
            if progress_callback:
                progress_callback(0, f"❌ 오류 발생: {str(e)}", [], 0)
            return False

    def run_homework_check(self, exam_id, progress_callback=None):
        """단일 과제 확인 프로세스 실행 (하위 호환성)"""
        # 기존 단일 시험 ID 처리를 위한 래퍼
        cohort_exam_ids = {'unknown': exam_id}
        return self.run_homework_check_multiple(cohort_exam_ids, progress_callback)

    def cleanup(self):
        self._add_log("클린업 프로세스 시작...")
        if self.driver:
            try:
                self.driver.quit()
                self._add_log("드라이버 종료 완료.")
            except Exception as e:
                self._add_log(f"드라이버 종료 중 오류: {e}")
        self.driver = None

def main():
    """메인 실행 함수 - 테스트용"""
    bot = HomeworkReminderBot()
    
    try:
        print("=== 과제 리마인더 봇 테스트 ===")
        print(f"로그인 정보: {bot.email}")
        
        # 시험 ID 입력 받기
        exam_id = input("확인할 시험 ID를 입력하세요: ")
        
        # 과제 확인 프로세스 실행
        result = bot.run_homework_check(exam_id)
        
        if result:
            print(f"\n=== 결과 요약 ===")
            print(f"전체 학생 수: {result['total_students']}명")
            print(f"제출 학생 수: {result['submitted_count']}명")
            print(f"미제출 학생 수: {result['non_submitted_count']}명")
            
            print(f"\n=== 제출한 학생 ===")
            for student in result['submitted']:
                print(f"✅ {student}")
            
            print(f"\n=== 미제출 학생 (리마인더 대상) ===")
            for student in result['non_submitted']:
                print(f"❌ {student}")
            
        else:
            print("과제 확인 프로세스 실행 실패")
        
    except Exception as e:
        print(f"오류가 발생했습니다: {e}")
        
    finally:
        bot.cleanup()
        print("프로그램을 종료합니다.")

if __name__ == "__main__":
    main()
