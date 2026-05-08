from flask import Flask, request
import urllib.parse
import subprocess

app = Flask(__name__)

def send_to_clipboard(text):
    # 使用 powershell 执行设置剪切板的操作
    # 这种方式对 Unicode（中文/特殊符号）支持极好，且不会触发内存溢出
    process = subprocess.Popen(
        ['powershell', '-command', 'Set-Clipboard -Value $Input'],
        stdin=subprocess.PIPE,
        encoding='utf-8'
    )
    process.communicate(input=text)

@app.route('/copy', methods=['GET'])
def copy_to_clipboard():
    msg = request.args.get('msg', '')
    if msg:
        # 解码并去除两端空格
        final_msg = urllib.parse.unquote(msg).strip()
        try:
            send_to_clipboard(final_msg)
            print(f"✅ 同步成功: {final_msg}")
            return "Success", 200
        except Exception as e:
            print(f"❌ 脚本执行错误: {e}")
            return str(e), 500
    return "No message", 400

if __name__ == '__main__':
    print("🚀 稳健版服务已启动 (PowerShell 模式)")
    # 你的局域网 IP
    app.run(host='0.0.0.0', port=5000)