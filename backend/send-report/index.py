import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Any, List
from datetime import datetime

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    '''
    Business: Send keyboard logger report via email with CSV attachment
    Args: event with httpMethod, body containing email and sessions data
    Returns: HTTP response with success/error status
    '''
    method: str = event.get('httpMethod', 'POST')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Max-Age': '86400'
            },
            'body': ''
        }
    
    if method != 'POST':
        return {
            'statusCode': 405,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Method not allowed'})
        }
    
    try:
        body_data = json.loads(event.get('body', '{}'))
        recipient_email: str = body_data.get('email', '')
        sessions: List[Dict[str, Any]] = body_data.get('sessions', [])
        
        if not recipient_email or not sessions:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Email and sessions are required'})
            }
        
        smtp_host = os.environ.get('SMTP_HOST')
        smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        smtp_user = os.environ.get('SMTP_USER')
        smtp_password = os.environ.get('SMTP_PASSWORD')
        
        if not all([smtp_host, smtp_user, smtp_password]):
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'SMTP configuration incomplete'})
            }
        
        csv_content = 'ID,Начало,Окончание,Длительность (сек),Количество клавиш\n'
        for session in sessions:
            csv_content += f"{session.get('id', '')},{session.get('startTime', '')},{session.get('endTime', 'В процессе')},{session.get('duration', 0)},{session.get('keyCount', 0)}\n"
        
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = recipient_email
        msg['Subject'] = f'Keyboard Logger - Отчёт от {datetime.now().strftime("%d.%m.%Y")}'
        
        body_text = f'''
Здравствуйте!

Во вложении находится CSV файл с историей сессий Keyboard Logger.

Всего сессий: {len(sessions)}
Дата формирования отчёта: {datetime.now().strftime("%d.%m.%Y %H:%M")}

С уважением,
Keyboard Logger
        '''
        
        msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
        
        attachment = MIMEBase('application', 'octet-stream')
        attachment.set_payload(csv_content.encode('utf-8'))
        encoders.encode_base64(attachment)
        attachment.add_header(
            'Content-Disposition',
            f'attachment; filename=keyboard-logger-{datetime.now().strftime("%Y-%m-%d")}.csv'
        )
        msg.attach(attachment)
        
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'isBase64Encoded': False,
            'body': json.dumps({
                'success': True,
                'message': f'Report sent to {recipient_email}'
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }
