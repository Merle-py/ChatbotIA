from flask import Flask, request, jsonify

from bot.ai_bot import AIBot
from services.waha import Waha
from services.memory import Memory


app = Flask(__name__)

memory = Memory(db_path='memory.db')


@app.route('/chatbot/webhook/', methods=['POST'])
def webhook():
    data = request.json
    chat_id = data['payload']['from']
    received_message = data['payload']['body']
    is_group = '@g.us' in chat_id
    is_status = 'status@broadcast'in chat_id

    if is_group or is_status:
        return jsonify({'status': 'success', 'message': 'Mensagem de grupo ou status ignorada.'}), 200

    waha = Waha()
    ai_bot = AIBot()

    # Salva a mensagem recebida na memória
    memory.save_message(chat_id, from_me=True, body=received_message)

    # Recupera o histórico persistente
    history_messages = memory.get_history(chat_id, limit=10)

    response_message = ai_bot.invoke(
        history_messages=history_messages,
        question=received_message,
    )

    # Salva a resposta do bot na memória
    memory.save_message(chat_id, from_me=False, body=response_message)

    waha.send_message(
        chat_id=chat_id,
        message=response_message,
    )
    waha.stop_typing(chat_id=chat_id)

    return jsonify({'status': 'success'}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
