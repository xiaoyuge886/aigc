#!/usr/bin/env python3
"""
Simple streaming test using requests library

This demonstrates real-time streaming output from the Agent API.
Run with: python tests/test_streaming_simple.py
"""
import json
import requests
import subprocess


def check_server_health() -> bool:
    """Check if server is healthy using curl"""
    try:
        result = subprocess.run(
            ["curl", "-s", "http://127.0.0.1:8000/api/v1/health"],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0 and b"healthy" in result.stdout:
            return True
    except Exception:
        pass
    return False


def test_stateless_stream():
    """Test single query with streaming output"""
    print("\n" + "=" * 60)
    print("TEST 1: Stateless Streaming Query (无状态流式查询)")
    print("=" * 60)

    print("\n📝 User: What is the capital of France?")
    print("\n🤖 Assistant (流式响应开始):\n")
    print("-" * 50)

    response = requests.post(
        "http://127.0.0.1:8000/api/v1/agent/query/stream",
        json={"prompt": "What is the capital of France?"},
        stream=True,
        timeout=120
    )

    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return

    chunk_count = 0
    text_buffer = ""

    for line in response.iter_lines():
        if not line.strip():
            continue

        line_str = line.decode('utf-8')

        if line_str.startswith("data: "):
            chunk_count += 1
            json_str = line_str[6:]

            try:
                data = json.loads(json_str)

                if data.get("type") == "data":
                    msg = data.get("data")

                    if msg and msg.get("content"):
                        for block in msg["content"]:
                            if block.get("type") == "text":
                                text = block.get("text", "")
                                print(text, end="", flush=True)
                                text_buffer += text

                    elif msg.get("subtype") in ["success", "error"]:
                        print(f"\n\n✅ 完成: {msg.get('subtype')}")
                        if msg.get("total_cost_usd"):
                            print(f"💰 成本: ${msg['total_cost_usd']:.4f}")
                        if msg.get("duration_ms"):
                            print(f"⏱️  耗时: {msg.get('duration_ms')}ms")

            except json.JSONDecodeError:
                pass

    print("\n" + "-" * 50)
    print(f"\n✅ 流式响应完成")
    print(f"   总chunk数: {chunk_count}")
    print(f"   总字符数: {len(text_buffer)}")


def test_session_stream():
    """Test session-based streaming conversation"""
    print("\n" + "=" * 60)
    print("TEST 2: Session Streaming Conversation (会话流式输出)")
    print("=" * 60)

    # Create session
    print("\n[Step 1] Creating session...")
    response = requests.post("http://127.0.0.1:8000/api/v1/session", json={"model": "haiku"})

    if response.status_code != 200:
        print(f"❌ Failed to create session: {response.status_code}")
        return

    session_id = response.json()["session_id"]
    print(f"✅ Session: {session_id}")

    # Send streaming query
    print("\n[Turn 1] User: Tell me a very short joke")
    print("\n🤖 Assistant (流式响应开始):\n")
    print("-" * 50)

    response = requests.post(
        f"http://127.0.0.1:8000/api/v1/session/{session_id}/query/stream",
        json={"prompt": "写个100字关于阿里巴巴新闻",  "incremental_stream": True,},
        stream=True,
        timeout=12000
    )

    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return

    chunk_count = 0
    text_buffer = ""

    for line in response.iter_lines(decode_unicode=True):
        print(line)
        if line.startswith("data: "):
            data = json.loads(line[6:])

            if data.get("type") == "text_delta":
                delta_count += 1
                text = data["data"]["text"]
                full_text += text
                print(text, end="", flush=True)

            elif data.get("type") == "data":
                msg = data["data"]
                if msg.get("type") == "result":
                    print(f"\n\n[结果] 轮次: {msg.get('num_turns')}")

    print("\n" + "-" * 50)
    print(f"\n✅ 流式响应完成")
    print(f"   总chunk数: {chunk_count}")
    print(f"   总字符数: {len(text_buffer)}")

    # Cleanup
    # requests.delete(f"http://127.0.0.1:8000/api/v1/session/{session_id}")
    # print("\n✅ Session deleted")


def main():
    print("\n" + "=" * 60)
    print("Claude Agent API - 流式输出测试 (requests版)")
    print("=" * 60)

    if not check_server_health():
        print("\n❌ Server not responding")
        print("Please start the server first: python main.py")
        return

    print("\n✅ Server is healthy\n")

    try:
        # test_stateless_stream()
        test_session_stream()

        print("\n" + "=" * 60)
        print("流式测试完成!")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
