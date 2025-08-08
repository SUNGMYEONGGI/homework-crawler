from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import os
from dotenv import load_dotenv
import time
import asyncio
from typing import List, Dict
import re
from collections import defaultdict

# 환경 변수 로드
load_dotenv()

class SlackBoltReminderBot:
    def __init__(self):
        # Slack 앱 토큰들
        self.bot_token = os.getenv("SLACK_BOT_TOKEN")
        self.app_token = os.getenv("SLACK_APP_TOKEN")
        
        if not self.bot_token:
            raise ValueError("SLACK_BOT_TOKEN이 설정되지 않았습니다. .env 파일을 확인해주세요.")
        
        if not self.app_token:
            raise ValueError("SLACK_APP_TOKEN이 설정되지 않았습니다. .env 파일을 확인해주세요.")
        
        # Slack Bolt 앱 초기화
        self.app = App(token=self.bot_token)
        
        # 이벤트 핸들러 등록
        self._register_handlers()
    
    def _register_handlers(self):
        """이벤트 핸들러들을 등록"""
        
        @self.app.event("app_mention")
        def handle_app_mention(event, say):
            """봇이 멘션되었을 때 응답"""
            say(f"안녕하세요! <@{event['user']}> 과제 리마인더 봇입니다! 🤖")
        
        @self.app.command("/homework_reminder")
        def handle_homework_command(ack, respond, command):
            """슬래시 커맨드 처리"""
            ack()
            respond("과제 리마인더 기능을 사용하려면 웹 인터페이스를 이용해주세요!")
        
        @self.app.event("message")
        def handle_message_events(body, logger):
            """메시지 이벤트 로깅 (필요시)"""
            logger.info(body)
    
    def _find_user_by_name(self, display_name: str) -> str:
        """
        사용자 표시 이름으로 슬랙 사용자 ID 찾기
        
        Args:
            display_name: 찾을 사용자의 표시 이름
            
        Returns:
            str: 사용자 ID 또는 원본 이름 (찾지 못한 경우)
        """
        try:
            # 모든 사용자 목록 가져오기
            response = self.app.client.users_list()
            
            if response['ok']:
                users = response['members']
                
                # 사용자 이름으로 검색 (여러 방식으로 매칭 시도)
                for user in users:
                    if user.get('deleted', False):  # 삭제된 사용자 제외
                        continue
                    
                    # 1. display_name으로 매칭
                    profile = user.get('profile', {})
                    if profile.get('display_name', '').strip() == display_name.strip():
                        return user['id']
                    
                    # 2. real_name으로 매칭
                    if profile.get('real_name', '').strip() == display_name.strip():
                        return user['id']
                    
                    # 3. username으로 매칭
                    if user.get('name', '').strip() == display_name.strip():
                        return user['id']
                    
                    # 4. first_name + last_name으로 매칭
                    first_name = profile.get('first_name', '')
                    last_name = profile.get('last_name', '')
                    full_name = f"{first_name}{last_name}".strip()
                    if full_name == display_name.strip():
                        return user['id']
                        
            return display_name  # 찾지 못하면 원본 이름 반환
            
        except Exception as e:
            print(f"사용자 ID 찾기 실패: {e}")
            return display_name  # 오류 시 원본 이름 반환

    def _parse_student_info(self, student_name: str) -> tuple:
        """
        학생 이름에서 기수와 실제 이름을 분리
        
        Args:
            student_name: "13 김철수" 또는 "김철수" 형태의 학생 이름
            
        Returns:
            tuple: (기수, 실제_이름) 또는 (None, 원본_이름)
        """
        try:
            # "숫자 이름" 패턴 매칭
            match = re.match(r'^(\d+)\s+(.+)$', student_name.strip())
            if match:
                term = match.group(1)  # 기수
                name = match.group(2)  # 실제 이름
                return (term, name)
            else:
                # 패턴이 맞지 않으면 원본 이름 반환
                return (None, student_name)
        except Exception as e:
            print(f"학생 정보 파싱 실패: {e}")
            return (None, student_name)

    def _group_students_by_term(self, students: List[str]) -> Dict[str, List[str]]:
        """
        학생들을 기수별로 그룹화
        
        Args:
            students: 학생 이름 리스트
            
        Returns:
            Dict: {기수: [학생이름들]} 형태의 딕셔너리
        """
        grouped = defaultdict(list)
        no_term_students = []
        
        for student in students:
            term, name = self._parse_student_info(student)
            if term:
                grouped[term].append(name)
            else:
                no_term_students.append(name)
        
        # 기수가 없는 학생들은 '기타' 그룹으로
        if no_term_students:
            grouped['기타'] = no_term_students
            
        return dict(grouped)

    def send_homework_reminder(self, exam_id: str, non_submitted_students: List[str], channel: str = None) -> dict:
        """
        미제출 학생들에게 과제 리마인더를 전송
        
        Args:
            exam_id: 시험 ID
            non_submitted_students: 미제출 학생 목록
            channel: 메시지를 보낼 채널 (기본값: #faq-bot-test)
            
        Returns:
            dict: 전송 결과
        """
        try:
            if not channel:
                channel = "#faq-bot-test"
            
            # 오늘 날짜 (YYMMDD 형식)
            today_date = time.strftime("%y%m%d")
            current_time = time.strftime("%Y-%m-%d %H:%M:%S")
            
            # 메인 메시지 작성 - 원하시는 형태로 변경
            main_message = f"[{today_date} 출결과제 진행 스레드]"
            
            # 메인 메시지 전송
            response = self.app.client.chat_postMessage(
                channel=channel,
                text=main_message
            )
            
            # 스레드에 미제출 학생들 태깅
            thread_ts = response["ts"]
            
            if non_submitted_students:
                # 학생들을 기수별로 그룹화
                grouped_students = self._group_students_by_term(non_submitted_students)
                
                # 기수별로 태깅 메시지 생성
                term_messages = []
                total_tagged_count = 0
                
                # 기수 순서대로 정렬 (숫자 기수들을 먼저 정렬하고, 기타는 마지막에)
                sorted_terms = []
                numeric_terms = []
                other_terms = []
                
                for term in grouped_students.keys():
                    if term.isdigit():
                        numeric_terms.append(int(term))
                    else:
                        other_terms.append(term)
                
                # 숫자 기수들을 오름차순으로 정렬
                numeric_terms.sort()
                sorted_terms = [str(term) for term in numeric_terms] + other_terms
                
                for term in sorted_terms:
                    students_in_term = grouped_students[term]
                    tagged_students_in_term = []
                    
                    for student_name in students_in_term:
                        # 실제 이름으로 슬랙 ID 찾기
                        user_id = self._find_user_by_name(student_name)
                        
                        # 실제 사용자 ID를 찾은 경우 <@USER_ID> 형태로, 못 찾은 경우 @이름 형태로
                        if user_id != student_name and user_id.startswith('U'):  # 슬랙 사용자 ID는 U로 시작
                            tagged_students_in_term.append(f"<@{user_id}>")
                        else:
                            tagged_students_in_term.append(f"@{student_name}")
                    
                    # 기수별 메시지 생성
                    if term == '기타':
                        term_line = f"기타 : {', '.join(tagged_students_in_term)}"
                    else:
                        term_line = f"{term}기 : {', '.join(tagged_students_in_term)}"
                    
                    term_messages.append(term_line)
                    total_tagged_count += len(students_in_term)
                
                # 전체 메시지 구성
                student_list_message = f"""🚨 **과제 미제출 학생 알림** 🚨

{chr(10).join(term_messages)}

📝 시험 ID `{exam_id}` 과제를 **오늘 23:59까지** 제출해주세요!
⏰ 마감시간이 얼마 남지 않았습니다."""
                
                # 슬랙 메시지 전송
                self.app.client.chat_postMessage(
                    channel=channel,
                    thread_ts=thread_ts,
                    text=student_list_message,
                    blocks=[
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"🚨 **과제 미제출 학생 알림** 🚨\n\n{chr(10).join(term_messages)}\n\n📝 시험 ID `{exam_id}` 과제를 **오늘 23:59까지** 제출해주세요!\n⏰ 마감시간이 얼마 남지 않았습니다."
                            }
                        }
                    ]
                )
     
            return {
                'success': True,
                'message': f'{len(non_submitted_students)}명에게 리마인더를 전송했습니다.',
                'channel': channel,
                'timestamp': current_time,
                'students_count': len(non_submitted_students),
                'thread_ts': thread_ts
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'슬랙 메시지 전송 실패: {str(e)}',
                'error': str(e)
            }
    
    def send_test_message(self, channel: str = None) -> dict:
        """
        테스트 메시지 전송
        
        Args:
            channel: 메시지를 보낼 채널
            
        Returns:
            dict: 전송 결과
        """
        try:
            if not channel:
                channel = "#faq-bot-test"
            
            test_message = "🤖 과제 리마인더 봇 테스트 메시지입니다!"
            
            response = self.app.client.chat_postMessage(
                channel=channel,
                text=test_message,
                blocks=[
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "🤖 테스트 메시지"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "과제 리마인더 봇이 정상적으로 작동하고 있습니다! ✅"
                        }
                    }
                ]
            )
            
            return {
                'success': True,
                'message': '테스트 메시지를 성공적으로 전송했습니다.',
                'channel': channel,
                'timestamp': response["ts"]
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'테스트 메시지 전송 실패: {str(e)}',
                'error': str(e)
            }
    
    def start_socket_mode(self):
        """Socket Mode로 앱 시작 (개발/테스트용)"""
        try:
            handler = SocketModeHandler(self.app, self.app_token)
            handler.start()
        except Exception as e:
            print(f"Socket Mode 시작 실패: {e}")
            raise


def main():
    """메인 실행 함수 - 테스트용"""
    try:
        print("=== Slack Bolt 리마인더 봇 테스트 ===")
        
        bot = SlackBoltReminderBot()
        
        # 테스트 메시지 전송
        result = bot.send_test_message("#general")  # 테스트 채널 변경 가능
        
        if result['success']:
            print(f"✅ {result['message']}")
        else:
            print(f"❌ {result['message']}")
        
        # 실제 리마인더 테스트 (주석 해제하여 사용)
        # test_students = ["13 김철수", "14 이영희", "13 박민수", "15 최진영", "14 홍길동"]
        # reminder_result = bot.send_homework_reminder("TEST001", test_students, "#general")
        # print(f"리마인더 결과: {reminder_result}")
        
        # 기수별 그룹화 테스트
        print("\n=== 기수별 그룹화 테스트 ===")
        test_students = ["13 김철수", "14 이영희", "13 박민수", "15 최진영", "14 홍길동", "김소영"]  # 마지막은 기수 없음
        grouped = bot._group_students_by_term(test_students)
        print(f"입력: {test_students}")
        print(f"그룹화 결과: {grouped}")
        
        print("\n=== 개별 파싱 테스트 ===")
        for student in test_students:
            term, name = bot._parse_student_info(student)
            print(f"{student} → 기수: {term}, 이름: {name}")
        
        print("\n=== 실제 슬랙 메시지 미리보기 ===")
        # 메시지 포맷 시뮬레이션
        term_messages = []
        for term in sorted([k for k in grouped.keys() if k != '기타']):
            students_in_term = grouped[term]
            tagged_students = [f"@{name}" for name in students_in_term]
            term_line = f"{term}기 : {', '.join(tagged_students)}"
            term_messages.append(term_line)
        
        if '기타' in grouped:
            students_in_term = grouped['기타']
            tagged_students = [f"@{name}" for name in students_in_term]
            term_line = f"기타 : {', '.join(tagged_students)}"
            term_messages.append(term_line)
        
        sample_message = f"""🚨 **과제 미제출 학생 알림** 🚨

{chr(10).join(term_messages)}

📝 시험 ID `TEST001` 과제를 **오늘 23:59까지** 제출해주세요!
⏰ 마감시간이 얼마 남지 않았습니다."""
        
        print(sample_message)
        
    except Exception as e:
        print(f"오류 발생: {e}")


if __name__ == "__main__":
    main()