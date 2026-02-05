# app/services/megaapi.py

import requests
import os
from typing import Dict, List, Optional
from datetime import datetime
from app import db


from dataclasses import dataclass, field


@dataclass
class Button:
    """Botao de acao rapida (ate 3 por mensagem)"""
    id: str
    title: str  # Max 20 caracteres


@dataclass
class ListSection:
    """Secao de uma lista interativa"""
    title: str
    rows: List[Dict]  # [{'id': '', 'title': '', 'description': ''}]


@dataclass
class ListMessage:
    """Mensagem com lista (ate 10 opcoes no total)"""
    body: str
    button_text: str
    sections: List[ListSection] = field(default_factory=list)


class MegapiService:
    """
    Servico completo de integracao com Megaapi (WhatsApp Business)
    """

    def __init__(self):
        self.base_url = os.getenv('MEGAAPI_BASE_URL', 'https://api.megaapi.com.br/v1')
        self.token = os.getenv('MEGAAPI_TOKEN')
        self.instance_key = os.getenv('MEGAAPI_INSTANCE_KEY', '')
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }

    def send_template_message(
        self,
        phone: str,
        template_name: str,
        variables: List[str],
        user_id: Optional[int] = None
    ) -> Dict:
        """
        Envia mensagem usando template aprovado

        Args:
            phone: Numero do destinatario (5511999999999)
            template_name: Nome do template (codigo no BD)
            variables: Lista de variaveis para substituir
            user_id: ID do usuario (para log)

        Returns:
            Resposta da API
        """
        from app.models import WhatsAppLog, WhatsAppTemplate

        # Buscar template no BD
        template = WhatsAppTemplate.query.filter_by(
            template_code=template_name,
            is_active=True
        ).first()

        if not template:
            raise Exception(f"Template '{template_name}' nao encontrado ou inativo")

        if template.megaapi_status != 'approved':
            raise Exception(f"Template '{template_name}' nao aprovado pela Megaapi")

        # Validar numero de telefone
        phone = self._format_phone(phone)

        # Preparar payload
        payload = {
            "phone": phone,
            "template": {
                "name": template_name,
                "language": "pt_BR",
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": var} for var in variables
                        ]
                    }
                ]
            }
        }

        try:
            response = requests.post(
                f"{self.base_url}/messages/template",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()

            # Salvar log
            self._log_message(
                phone=phone,
                template_name=template_name,
                user_id=user_id,
                status='sent',
                message_id=result.get('id'),
                response_json=result
            )

            # Incrementar contador
            template.send_count += 1
            db.session.commit()

            return result

        except requests.exceptions.RequestException as e:
            # Log de erro
            self._log_message(
                phone=phone,
                template_name=template_name,
                user_id=user_id,
                status='failed',
                error_message=str(e)
            )

            raise Exception(f"Erro ao enviar mensagem WhatsApp: {str(e)}")

    def send_custom_message(
        self,
        phone: str,
        message: str,
        user_id: Optional[int] = None
    ) -> Dict:
        """
        Envia mensagem de texto simples (apenas dentro da janela de 24h)
        """
        phone = self._format_phone(phone)

        payload = {
            "phone": phone,
            "message": message
        }

        try:
            response = requests.post(
                f"{self.base_url}/messages/text",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()

            self._log_message(
                phone=phone,
                template_name='custom_text',
                user_id=user_id,
                status='sent',
                message_id=result.get('id'),
                response_json=result
            )

            return result

        except requests.exceptions.RequestException as e:
            self._log_message(
                phone=phone,
                template_name='custom_text',
                user_id=user_id,
                status='failed',
                error_message=str(e)
            )

            raise Exception(f"Erro ao enviar mensagem: {str(e)}")

    def send_buttons(
        self,
        phone: str,
        message: str,
        buttons: List[Button],
        user_id: Optional[int] = None
    ) -> Dict:
        """
        Envia mensagem com botoes de acao rapida (max 3)
        """
        if len(buttons) > 3:
            raise ValueError("Maximo de 3 botoes permitido")

        phone = self._format_phone(phone)

        # Formato esperado pela MegaAPI v1 para botoes
        # Nota: Adaptando conforme o esperado pelo backend da academia
        payload = {
            "messageData": {
                "to": phone,
                "text": message,
                "buttons": [
                    {"buttonId": btn.id, "buttonText": {"displayText": btn.title}, "type": 1}
                    for btn in buttons
                ],
                "headerType": 1
            }
        }

        try:
            url = f"{self.base_url}/sendMessage/{self.instance_key}/buttonsMessage"

            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()

            self._log_message(
                phone=phone,
                template_name='button_message',
                user_id=user_id,
                status='sent',
                message_id=result.get('id'),
                response_json=result
            )

            return result

        except requests.exceptions.RequestException as e:
            self._log_message(
                phone=phone,
                template_name='button_message',
                user_id=user_id,
                status='failed',
                error_message=str(e)
            )

            raise Exception(f"Erro ao enviar button message: {str(e)}")

    def send_list_message(
        self,
        phone: str,
        text: str,
        button_text: str,
        sections: List[dict],
        user_id: Optional[int] = None
    ) -> Dict:
        """
        Envia mensagem com menu interativo (List Message).

        Args:
            phone: Numero do destinatario
            text: Texto principal da mensagem
            button_text: Texto do botao que abre a lista
            sections: Lista de secoes com opcoes
            user_id: ID do usuario (para log)

        Formato sections:
        [
            {
                "title": "Acoes",
                "rows": [
                    {
                        "title": "Confirmar",
                        "rowId": "confirm_123",
                        "description": "Garantir vaga"
                    }
                ]
            }
        ]

        Returns:
            Resposta da API
        """
        phone = self._format_phone(phone)

        payload = {
            "messageData": {
                "to": phone,
                "text": text,
                "buttonText": button_text,
                "title": "Acao Necessaria",
                "description": "Selecione uma opcao",
                "sections": sections,
                "listType": 0
            }
        }

        try:
            # Endpoint para List Message
            url = f"{self.base_url}/sendMessage/{self.instance_key}/listMessage"

            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()

            self._log_message(
                phone=phone,
                template_name='list_message',
                user_id=user_id,
                status='sent',
                message_id=result.get('id'),
                response_json=result
            )

            return result

        except requests.exceptions.RequestException as e:
            self._log_message(
                phone=phone,
                template_name='list_message',
                user_id=user_id,
                status='failed',
                error_message=str(e)
            )

            raise Exception(f"Erro ao enviar list message: {str(e)}")

    def send_bulk_messages(
        self,
        recipients: List[Dict]
    ) -> Dict:
        """
        Envia mensagens em massa

        Args:
            recipients: Lista de destinatarios
            Exemplo:
            [
                {
                    "phone": "5511999999999",
                    "template_name": "promocao",
                    "variables": ["Black Friday", "50% OFF"],
                    "user_id": 123
                },
                ...
            ]

        Returns:
            Resumo do envio
        """

        results = {
            "total": len(recipients),
            "success": 0,
            "failed": 0,
            "errors": []
        }

        for recipient in recipients:
            try:
                self.send_template_message(
                    phone=recipient["phone"],
                    template_name=recipient["template_name"],
                    variables=recipient["variables"],
                    user_id=recipient.get("user_id")
                )
                results["success"] += 1

            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "phone": recipient["phone"],
                    "error": str(e)
                })

        return results

    def get_message_status(self, message_id: str) -> Dict:
        """
        Consulta status de mensagem enviada
        """
        try:
            response = requests.get(
                f"{self.base_url}/messages/{message_id}",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro ao consultar status: {str(e)}")

    def get_template_status(self, template_code: str) -> str:
        """
        Consulta status de aprovacao de um template
        """
        try:
            response = requests.get(
                f"{self.base_url}/templates/{template_code}",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()
            return data.get('status', 'unknown')

        except:
            return 'unknown'

    def send_template(
        self,
        phone: str,
        template_name: str,
        language: str = "pt_BR",
        components: Optional[List[Dict]] = None,
        user_id: Optional[int] = None
    ) -> Dict:
        """
        Envia template pre-aprovado pelo Meta (formato v2).

        Args:
            phone: Numero com DDI (ex: 5527999999999)
            template_name: Nome do template cadastrado no Meta
            language: Codigo do idioma (padrao: pt_BR)
            components: Parametros do template
            user_id: ID do usuario (para log)

        Example:
            components = [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": "Joao"},
                        {"type": "text", "text": "15/02/2026"}
                    ]
                }
            ]
        """
        phone = self._format_phone(phone)

        payload = {
            "messageData": {
                "to": phone,
                "template": {
                    "name": template_name,
                    "language": {"code": language},
                    "components": components or []
                }
            }
        }

        try:
            url = f"{self.base_url}/sendMessage/{self.instance_key}/templateMessage"

            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()

            self._log_message(
                phone=phone,
                template_name=template_name,
                user_id=user_id,
                status='sent',
                message_id=result.get('id'),
                response_json=result
            )

            return {'success': True, 'message_id': result.get('id'), 'data': result}

        except requests.exceptions.RequestException as e:
            self._log_message(
                phone=phone,
                template_name=template_name,
                user_id=user_id,
                status='failed',
                error_message=str(e)
            )
            return {'success': False, 'error': str(e)}

    def _format_phone(self, phone: str) -> str:
        """
        Formata numero para padrao internacional
        Entrada: (11) 99999-9999 ou 11999999999
        Saida: 5511999999999
        """
        # Remover tudo que nao e numero
        phone = ''.join(filter(str.isdigit, phone))

        # Adicionar codigo do pais
        if not phone.startswith('55'):
            phone = '55' + phone

        # Validar tamanho (55 + DDD + 9 digitos)
        if len(phone) != 13:
            raise ValueError(f"Numero de telefone invalido: {phone}")

        return phone

    def _log_message(
        self,
        phone: str,
        template_name: str,
        user_id: Optional[int] = None,
        status: str = 'sent',
        message_id: Optional[str] = None,
        response_json: Optional[Dict] = None,
        error_message: Optional[str] = None
    ):
        """
        Salva log de mensagem no banco
        """
        from app.models import WhatsAppLog

        log = WhatsAppLog(
            user_id=user_id,
            phone=phone,
            template_name=template_name,
            status=status,
            message_id=message_id,
            response_json=response_json,
            error_message=error_message,
            sent_at=datetime.utcnow()
        )

        db.session.add(log)
        db.session.commit()


# Singleton
megaapi = MegapiService()
