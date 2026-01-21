"""测试增量流式功能"""
import requests
import json



def test_session_incremental_streaming():
    """测试会话的增量流式功能"""

    print("=" * 60)
    print("测试: 会话增量流式 (incremental_stream=True)")
    print("=" * 60)

    # 方式1: 可以预先创建会话（可选）
    # response = requests.post(
    #     "http://localhost:8000/api/v1/session",
    #     json={
    #         "incremental_stream": True,
    #     },
    #     timeout=10
    # )
    #
    # if response.status_code != 200:
    #     print(f"创建会话失败: {response.status_code}")
    #     return
    #
    # session_data = response.json()
    # session_id = session_data["session_id"]
    # print(f"\n创建会话: {session_id}")

    # 方式2: 直接开始对话，无需预先创建会话（推荐）
    session_id = None  # 第一次查询时不传 session_id
    print("\n直接开始对话（无需预先创建会话）...")

    # 发送增量流式查询（多轮对话测试）
    print("\n发送查询...")

    for i in range(2):
        if i == 0:
            # 第一次查询
            prompt = "你有哪些skill，详细介绍一下 Python"
            print(f"\n[第 {i+1} 次查询] {prompt}")
        else:
            # 第二次查询
            prompt = "输出一个echarts demo图"
            print(f"\n[第 {i+1} 次查询] {prompt}")

        response = requests.post(
            "http://localhost:8000/api/v1/session/query/stream",  # 新 API
            json={
                "prompt": prompt,
                "session_id": session_id,  # 第一次为 None，后续使用返回的 session_id
                "incremental_stream": True,
            },
            stream=True,
            timeout=300
        )

        print(f"状态码: {response.status_code}\n")

        delta_count = 0
        full_text = ""

        for line in response.iter_lines(decode_unicode=True):
            if line.startswith("data: "):
                data = json.loads(line[6:])

                if data.get("type") == "text_delta":
                    # 增量文本片段
                    delta_count += 1
                    text = data["data"]["text"]
                    full_text += text
                    print(text, end="", flush=True)

                elif data.get("type") == "data":
                    msg = data["data"]
                    if msg.get("type") == "result":
                        print(f"\n\n[结果] 轮次: {msg.get('num_turns')}")
                        # 提取 session_id 用于后续查询
                        if session_id is None and msg.get("session_id"):
                            session_id = msg.get("session_id")
                            print(f"[会话ID] {session_id}")

        print(f"\n\n收到 {delta_count} 个增量片段")

    # # 3. 清理会话（如果需要）
    # if session_id:
    #     requests.delete(f"http://localhost:8000/api/v1/session/{session_id}")
    #     print(f"\n会话 {session_id} 已删除")


if __name__ == "__main__":
    print("开始测试增量流式功能...\n")

    try:
        # test_incremental_streaming()
        # print("\n" + "=" * 60)
        test_session_incremental_streaming()
        print("\n" + "=" * 60)
        print("✅ 所有测试完成！")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
