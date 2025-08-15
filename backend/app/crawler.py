from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import os
import json
import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString
import asyncio


class FastCampusLMSCrawler:
    def __init__(self):
        self.email = os.getenv("FASTCAMPUS_EMAIL", "")
        self.password = os.getenv("FASTCAMPUS_PASSWORD", "")
        self.driver = None
        self.wait = None
        self.is_running = False
        self.current_exam_id = None
        self.collected_data = []
        self.log_messages = []

        if not self.email or not self.password:
            self._add_log("⚠️ 경고: 로그인 정보가 설정되지 않았습니다. 환경변수 FASTCAMPUS_EMAIL, FASTCAMPUS_PASSWORD를 설정하세요.")

    def _add_log(self, message):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.log_messages.append(log_entry)

    def setup_driver(self):
        self._add_log("Selenium 드라이버 설정 시작...")
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_experimental_option(
            "prefs",
            {
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False,
                "autofill.profile_enabled": False,
            },
        )

        # Railway의 Docker 환경에서 chromium이 설치되어 있을 수 있으므로 우선 시스템 chromedriver 시도
        try:
            self._add_log("시스템 chromedriver 사용 시도...")
            service = Service()  # PATH 에서 chromedriver 검색
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 20)
            self._add_log("시스템 chromedriver로 드라이버 설정 완료.")
            return
        except Exception as e2:
            self._add_log(f"시스템 chromedriver 실패: {e2}")

        # 실패 시 webdriver_manager로 드라이버 설치 시도
        try:
            chrome_driver_manager = ChromeDriverManager(cache_valid_range=7, path="/tmp/chromedriver")
            driver_path = chrome_driver_manager.install()
            self._add_log(f"ChromeDriver 경로: {driver_path}")

            if not os.path.isfile(driver_path) or not os.access(driver_path, os.X_OK):
                raise Exception(f"ChromeDriver 파일이 없거나 실행 권한이 없습니다: {driver_path}")

            service = Service(driver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 20)
            self._add_log("Selenium 드라이버 설정 완료.")
        except Exception as e:
            error_msg = str(e) if str(e) else f"타입: {type(e).__name__}"
            self._add_log(f"ChromeDriver 설정 실패: {error_msg}")
            self._add_log(f"예외 세부정보: {repr(e)}")
            raise

    def login_process(self):
        self._add_log("로그인 프로세스 시작...")

        if not self.email or not self.password:
            error_msg = "로그인 정보가 없습니다. 환경변수 FASTCAMPUS_EMAIL, FASTCAMPUS_PASSWORD를 설정하세요."
            self._add_log(f"❌ {error_msg}")
            raise Exception(error_msg)

        if self.driver:
            try:
                self.driver.quit()
                self._add_log("기존 드라이버 종료.")
            except Exception as e:
                self._add_log(f"기존 드라이버 종료 중 오류 (무시): {e}")

        self.setup_driver()

        try:
            self._add_log("로그인 페이지로 이동...")
            self.driver.get("https://lmsadmin-kdt.fastcampus.co.kr/sign-in")

            # 사이트 선택
            site_select = self.wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="site"]')))
            Select(site_select).select_by_index(0)
            time.sleep(0.2)

            # 이메일 입력
            email_input = self.wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="userName"]')))
            email_input.clear()
            email_input.send_keys(self.email)

            # 비밀번호 입력
            password_input = self.wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="password"]')))
            password_input.clear()
            password_input.send_keys(self.password)

            # 로그인 버튼 클릭
            login_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/main/section/div/form/button'))
            )
            self.driver.execute_script("arguments[0].click();", login_button)

            # 로그인 완료 대기
            self.wait.until(
                lambda drv: drv.current_url != "https://lmsadmin-kdt.fastcampus.co.kr/sign-in"
            )
            self._add_log("로그인 성공!")

            current_url = self.driver.current_url
            self.driver.execute_script("window.open('', '_blank');")
            time.sleep(0.2)
            if len(self.driver.window_handles) > 1:
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[-1])
            self.driver.get(current_url)
            time.sleep(1)
            return True
        except Exception as e:
            error_msg = str(e) if str(e) else f"알 수 없는 오류 (타입: {type(e).__name__})"
            self._add_log(f"❌ 로그인 실패: {error_msg}")
            self._add_log(f"예외 세부정보: {repr(e)}")
            if self.driver:
                try:
                    self.driver.quit()
                except Exception:
                    pass
            self.driver = None
            raise

    def _collect_data_item(self, student_name, blog_link):
        self.collected_data.append({"수강자 이름": student_name, "블로그 링크": blog_link})

    def export_data(self, exam_id, file_format="csv"):
        if not self.collected_data:
            self._add_log("내보낼 데이터가 없습니다.")
            return None

        df = pd.DataFrame(self.collected_data)
        timestamp_str = time.strftime("%Y%m%d_%H%M%S")
        base_filename = f"exam_data_{exam_id}_{timestamp_str}"
        output_path = None

        try:
            if file_format == "csv":
                output_path = f"{base_filename}.csv"
                df.to_csv(output_path, index=False, encoding="utf-8-sig")
            elif file_format == "xlsx":
                output_path = f"{base_filename}.xlsx"
                df.to_excel(output_path, index=False, engine="openpyxl")
            elif file_format == "json":
                output_path = f"{base_filename}.json"
                df.to_json(output_path, orient="records", lines=False, indent=4, force_ascii=False)
            elif file_format == "xml":
                output_path = f"{base_filename}.xml"
                root = ET.Element("students")
                for _, row in df.iterrows():
                    student_elem = ET.SubElement(root, "student")
                    ET.SubElement(student_elem, "name").text = str(row["수강자 이름"])
                    ET.SubElement(student_elem, "blog_link").text = str(row["블로그 링크"]) 
                xml_str = ET.tostring(root, encoding="utf-8")
                pretty_xml_str = parseString(xml_str).toprettyxml(indent="  ")
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(pretty_xml_str)
            else:
                self._add_log(f"지원하지 않는 파일 형식: {file_format}")
                return None
            self._add_log(f"{output_path} 파일로 데이터 내보내기 완료.")
            return output_path
        except Exception as e:
            self._add_log(f"데이터 내보내기 중 오류 ({output_path}): {e}")
            return None

    async def crawl_exam_data_async(self, exam_id, progress_callback, log_callback):
        self.current_exam_id = exam_id
        self.collected_data = []
        self.log_messages = []
        self.is_running = True

        async def update_log_and_progress(progress_value, desc_message):
            self._add_log(desc_message)
            await log_callback(desc_message)
            await progress_callback(progress_value, desc_message)

        base_url = "https://lmsadmin-kdt.fastcampus.co.kr/exams/"
        target_url = f"{base_url}{exam_id}/detail"

        await update_log_and_progress(0.3, f"시험 ID {exam_id} 페이지로 이동 중: {target_url}")
        self.driver.get(target_url)
        await asyncio.sleep(1)

        total_count = 0
        try:
            pagination_element_xpath = '//*[@id="app"]/main/section/div/div[2]/div/div[2]/div[2]/span[2]'
            pagination_element = self.wait.until(EC.presence_of_element_located((By.XPATH, pagination_element_xpath)))
            pagination_text = pagination_element.text.strip()
            if "/" in pagination_text:
                total_count = int(pagination_text.split("/")[1].strip())
            else:
                total_count = int(pagination_text)
            if total_count <= 0:
                total_count = 1
            await update_log_and_progress(0.35, f"총 {total_count}개 항목 확인.")
        except Exception as e_page:
            total_count = 1
            await update_log_and_progress(0.35, f"페이지네이션 분석 실패 ({e_page}), 단일 항목 처리 시도.")

        collected_data_count_local = 0
        for i in range(total_count):
            if not self.is_running:
                break

            current_progress_val = 0.4 + (i / total_count) * 0.5
            await update_log_and_progress(current_progress_val, f"{i + 1}/{total_count} 번째 항목 처리 시작...")

            try:
                student_name_element_xpath = '//*[@id="app"]/main/section/div/div[2]/div/div[2]/div[1]/strong'
                student_name_element = self.wait.until(
                    EC.visibility_of_element_located((By.XPATH, student_name_element_xpath))
                )
                student_name = student_name_element.text.strip()
                await update_log_and_progress(current_progress_val, f"이름: {student_name}")

                blog_link = ""
                try:
                    answer_view_button_xpath = '//*[@id="app"]/main/section/div/div[2]/div/div[4]/div/div/table/tbody/tr/td[6]/button'
                    answer_view_button = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, answer_view_button_xpath))
                    )
                    self.driver.execute_script("arguments[0].click();", answer_view_button)
                    await update_log_and_progress(current_progress_val, "과제 내용 보기 버튼 클릭.")
                    await asyncio.sleep(0.5)

                    blog_link_element_xpath = '//*[@id=\"modals\"]/section/div/div/div/div[2]/ul/li[2]/div/p'
                    blog_link_element = self.wait.until(
                        EC.visibility_of_element_located((By.XPATH, blog_link_element_xpath))
                    )
                    blog_link = blog_link_element.text.strip()
                    await update_log_and_progress(
                        current_progress_val, f"블로그 링크/내용 수집: {blog_link[:50] if blog_link else ''}..."
                    )

                    close_modal_xpath_1 = '//*[@id="modals"]/section/div/div/div/div[1]/button'
                    close_modal_button_1 = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, close_modal_xpath_1))
                    )
                    self.driver.execute_script("arguments[0].click();", close_modal_button_1)
                    await update_log_and_progress(current_progress_val, "첫 번째 모달 닫기.")
                    await asyncio.sleep(0.5)
                except TimeoutException:
                    await update_log_and_progress(
                        current_progress_val, f"{student_name}: 블로그 링크 수집 중 Timeout (항목 없음 가능성)"
                    )
                except Exception as e_blog:
                    await update_log_and_progress(
                        current_progress_val, f"{student_name}: 블로그 링크 수집 중 오류 - {e_blog}"
                    )

                self._collect_data_item(student_name, blog_link)
                collected_data_count_local += 1

                try:
                    close_modal_xpath_2 = '//*[@id="modals"]/section[2]/div/div/section/div/button[2]'
                    close_modal_button_2 = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable((By.XPATH, close_modal_xpath_2))
                    )
                    self.driver.execute_script("arguments[0].click();", close_modal_button_2)
                    await update_log_and_progress(current_progress_val, "두 번째 모달 닫기.")
                    await asyncio.sleep(0.5)
                except TimeoutException:
                    pass
                except Exception as e_modal2:
                    await update_log_and_progress(
                        current_progress_val, f"{student_name}: 두 번째 모달 닫기 중 오류 - {e_modal2}"
                    )

                if i < total_count - 1:
                    next_button_xpath = '//*[@id="app"]/main/section/div/div[2]/div/div[2]/div[2]/button[2]'
                    next_button = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, next_button_xpath))
                    )
                    self.driver.execute_script("arguments[0].click();", next_button)
                    await update_log_and_progress(current_progress_val, "다음 항목으로 이동.")
                    await asyncio.sleep(1)

            except Exception as e_item:
                await update_log_and_progress(current_progress_val, f"{i + 1}번째 항목 처리 중 주 오류: {e_item}")
                if i < total_count - 1:
                    try:
                        next_button_xpath_err = '//*[@id="app"]/main/section/div/div[2]/div/div[2]/div[2]/button[2]'
                        next_button_err = self.wait.until(
                            EC.element_to_be_clickable((By.XPATH, next_button_xpath_err))
                        )
                        self.driver.execute_script("arguments[0].click();", next_button_err)
                        await update_log_and_progress(current_progress_val, "오류 후 다음 항목 강제 이동 시도.")
                        await asyncio.sleep(1)
                    except Exception as e_next_err:
                        await update_log_and_progress(current_progress_val, f"강제 이동 중 추가 오류({e_next_err}). 중단.")
                        break
                continue

        await update_log_and_progress(0.9, f"크롤링 완료. 총 {collected_data_count_local}개 데이터 수집.")
        return collected_data_count_local

    def cleanup(self):
        self._add_log("클린업 프로세스 시작...")
        if self.driver:
            try:
                self.driver.quit()
                self._add_log("드라이버 종료 완료.")
            except Exception as e:
                self._add_log(f"드라이버 종료 중 오류: {e}")
        self.driver = None
        self.is_running = False
        self.current_exam_id = None


