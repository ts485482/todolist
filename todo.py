import streamlit as st 
import firebase_admin
from firebase_admin import credentials, firestore
import time
import json

key_dict = json.loads(st.secrets["firebase_key"])
cred = credentials.Certificate(key_dict)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()


if "login" not in st.session_state:
    st.session_state["login"] = False

if st.session_state["login"]:
    st.title("A팀 할 일 목록")

else:
    tab1, tab2 = st.tabs(["로그인","회원가입"])
    with tab1:
        st.header("로그인")
        todo_login_id=st.text_input("ID", key = "todo_login_id")
        todo_login_pw=st.text_input("PW", type = "password", key = "todo_login_pw")

        if st.button("로그인"):
            if not todo_login_id or not todo_login_pw:
                st.warning("아이디 또는 비밀번호를 입력해주세요.")
        
            else:
                user_doc = db.collection("todo_users").document(todo_login_id).get()
                if user_doc.exists and user_doc.to_dict()["password"] == todo_login_pw:
                    st.session_state["login"] = True
                    st.session_state["todo_user_id"] = todo_login_id
                    st.session_state["todo_user_name"] = user_doc.to_dict()["username"]
                    st.success("로그인 성공!")
                    st.rerun()
                else:
                    st.error("아이디 또는 비밀번호가 일치하지 않습니다.")

    with tab2:
        st.header("회원가입")
        username = st.text_input("이름", key="username")
        new_id = st.text_input("사용할 아이디", key="new_id")
        new_pw = st.text_input("사용할 비밀번호", type="password", key="new_pw")
        confirm_pw = st.text_input("비밀번호 확인", type="password", key="confirm_pw")

        if st.button("회원가입"):
            if new_pw != confirm_pw:
                st.error("비밀번호가 일치하지 않습니다.")

            elif not username:
                st.error("성함을 입력해주세요.")
            
            elif not new_id or not new_pw:
                st.error("아이디 또는 비밀번호를 입력해주세요.")

            else:
                db.collection("todo_users").document(new_id).set({"username": username, "password": new_pw})
                st.success("회원가입 완료! 로그인 탭에서 접속하세요.")
                st.rerun()

if st.session_state["login"]:
    st.write(f"환영합니다, {st.session_state["todo_user_name"]}님!")

    with st.sidebar:
        if st.button("로그아웃"):
            st.session_state["login"] = False
            st.rerun()

        if "delete_account" not in st.session_state:
            st.session_state["delete_account"] = False

        if not st.session_state["delete_account"]:
            if st.button("계정 삭제", key="delete"):
                st.session_state["delete_account"] = True

        else:
            st.warning("계정을 삭제하시겠습니까?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("삭제", key="confirm_delete"):
                    db.collection("todo_users").document(st.session_state["todo_user_id"]).delete()
                    st.session_state["login"] = False
                    st.session_state["delete_account"] = False
                    st.rerun()

            with col2:
                if st.button("취소", key="cancel_delete"):
                    st.session_state["delete_account"] = False
                    st.rerun()

    with st.form("with_todos"):
            st.subheader("할 일 추가")
            selbox = st.selectbox("카테고리",["팀플","개인"])
            task = st.text_input("할 일을 적으세요.")
            if st.form_submit_button("추가"):
                if task:
                    db.collection("with_todos").add({
                        "todo_user_id": st.session_state["todo_user_id"],
                        "todo_user_name": st.session_state["todo_user_name"],
                        "category": selbox,
                        "task": task,
                        "completed": False
                    })
                    st.rerun()
                else:
                    st.warning("할 일을 입력하세요.")

    st.divider()
    st.subheader("금일 할 일 목록")

    todocs = db.collection("with_todos").stream()

    selected_tasks = []

    with st.form("todo_list_form"):
        for todoc in todocs:
            todo = todoc.to_dict()
            if todo["todo_user_id"] == st.session_state["todo_user_id"]:
                is_checked = st.checkbox(
                    f"[{todo['category']}] {todo['task']}", 
                    key=f"check_{todoc.id}"
                )
                if is_checked:
                    selected_tasks.append(todoc.id)
            else:
                st.text(f"🔒 {todo.get('todo_user_name', '알수없음')} : {todo['category']} - {todo['task']}")
        
        submit_done = st.form_submit_button("선택한 항목 완료 및 삭제")

    if submit_done:
        if not selected_tasks:
            st.warning("완료할 항목을 선택해주세요.")
        else:
            for doc_id in selected_tasks:
                db.collection("with_todos").document(doc_id).delete()
            st.balloons()
            st.success(f"{len(selected_tasks)}개의 할 일을 완료했습니다!")
            time.sleep(2)
            st.rerun()