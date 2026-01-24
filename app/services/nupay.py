# app/services/nupay.py

"""
Serviço de integração com API NuPay (Nubank Business).
Documentação: https://api.spinpay.com.br/docs
"""

import requests
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from flask import current_app


logger = logging.getLogger(__name__)


class NuPayService:
    """
    Cliente para API NuPay - Pagamentos PIX e Recorrência.
    """

    def __init__(self):
        """Inicializa o serviço com credenciais do config."""
        self.base_url = current_app.config.get('NUPAY_BASE_URL', 'https://api.spinpay.com.br')
        self.headers = {
            'X-Merchant-Key': current_app.config.get('NUPAY_MERCHANT_KEY', ''),
            'X-Merchant-Token': current_app.config.get('NUPAY_MERCHANT_TOKEN', ''),
            'Content-Type': 'application/json'
        }

    def create_pix_payment(self, payment, user) -> Dict:
        """
        Cria um pagamento PIX instantâneo.

        Args:
            payment: Payment model instance
            user: User model instance

        Returns:
            dict com pspReferenceId, paymentUrl, qrCode, pixCopyPaste

        Raises:
            NuPayError: Se houver erro na API
        """
        url = f"{self.base_url}/v1/checkouts/payments"

        # Separar nome em primeiro e último
        name_parts = user.name.split()
        first_name = name_parts[0] if name_parts else user.name
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else first_name

        # Remover formatação do CPF
        cpf_clean = user.cpf.replace('.', '').replace('-', '') if user.cpf else ''

        # URL base para callbacks
        base_url = current_app.config.get('BASE_URL', 'http://localhost:5000')

        payload = {
            "referenceId": f"PAYMENT_{payment.id}",
            "amount": {
                "value": float(payment.amount),
                "currency": "BRL"
            },
            "paymentMethod": {
                "type": "nupay",
                "authorizationType": "manually_authorized"
            },
            "shopper": {
                "firstName": first_name,
                "lastName": last_name,
                "document": cpf_clean,
                "email": user.email,
                "phone": self._format_phone(user.phone)
            },
            "paymentFlow": {
                "returnUrl": f"{base_url}/shop/checkout/success",
                "cancelUrl": f"{base_url}/shop/checkout/cancel"
            },
            "expiresAt": (datetime.utcnow() + timedelta(minutes=15)).isoformat() + "Z"
        }

        try:
            logger.info(f"Criando PIX para Payment #{payment.id}")

            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()
            logger.info(f"PIX criado com sucesso: {result.get('pspReferenceId')}")

            return result

        except requests.exceptions.HTTPError as e:
            error_msg = f"Erro HTTP ao criar PIX: {e.response.status_code}"
            try:
                error_detail = e.response.json()
                error_msg += f" - {error_detail}"
            except:
                pass
            logger.error(error_msg)
            raise NuPayError(error_msg)

        except requests.exceptions.RequestException as e:
            error_msg = f"Erro de conexão ao criar PIX: {str(e)}"
            logger.error(error_msg)
            raise NuPayError(error_msg)

    def get_payment_status(self, psp_reference_id: str) -> Dict:
        """
        Consulta status de um pagamento.

        Args:
            psp_reference_id: ID do pagamento na NuPay

        Returns:
            dict com status atual do pagamento
        """
        url = f"{self.base_url}/v1/checkouts/payments/{psp_reference_id}"

        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()

            return response.json()

        except requests.exceptions.HTTPError as e:
            error_msg = f"Erro ao consultar status: {e.response.status_code}"
            logger.error(error_msg)
            raise NuPayError(error_msg)

        except requests.exceptions.RequestException as e:
            error_msg = f"Erro de conexão ao consultar status: {str(e)}"
            logger.error(error_msg)
            raise NuPayError(error_msg)

    def create_recurring_subscription(self, subscription, user) -> Dict:
        """
        Cria uma assinatura recorrente (CIBA flow).
        O cliente receberá notificação no app Nubank para autorizar.

        Args:
            subscription: Subscription model instance
            user: User model instance

        Returns:
            dict com subscriptionId, authorizationUrl
        """
        url = f"{self.base_url}/v1/subscriptions"

        # Separar nome
        name_parts = user.name.split()
        first_name = name_parts[0] if name_parts else user.name

        # CPF limpo
        cpf_clean = user.cpf.replace('.', '').replace('-', '') if user.cpf else ''

        # URL base
        base_url = current_app.config.get('BASE_URL', 'http://localhost:5000')

        # Intervalo de cobrança do pacote
        interval_days = subscription.package.recurring_interval_days or 30

        payload = {
            "referenceId": f"SUB_{subscription.id}",
            "amount": {
                "value": float(subscription.package.price),
                "currency": "BRL"
            },
            "interval": {
                "unit": "day",
                "length": interval_days
            },
            "shopper": {
                "firstName": first_name,
                "document": cpf_clean,
                "email": user.email,
                "phone": self._format_phone(user.phone)
            },
            "paymentFlow": {
                "returnUrl": f"{base_url}/student/subscription/{subscription.id}",
                "cancelUrl": f"{base_url}/student/subscriptions"
            }
        }

        try:
            logger.info(f"Criando assinatura recorrente para Subscription #{subscription.id}")

            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()
            logger.info(f"Assinatura recorrente criada: {result.get('subscriptionId')}")

            return result

        except requests.exceptions.HTTPError as e:
            error_msg = f"Erro ao criar assinatura recorrente: {e.response.status_code}"
            try:
                error_detail = e.response.json()
                error_msg += f" - {error_detail}"
            except:
                pass
            logger.error(error_msg)
            raise NuPayError(error_msg)

        except requests.exceptions.RequestException as e:
            error_msg = f"Erro de conexão ao criar assinatura: {str(e)}"
            logger.error(error_msg)
            raise NuPayError(error_msg)

    def cancel_subscription(self, nupay_subscription_id: str) -> Dict:
        """
        Cancela uma assinatura recorrente.

        Args:
            nupay_subscription_id: ID da assinatura na NuPay

        Returns:
            dict com status do cancelamento
        """
        url = f"{self.base_url}/v1/subscriptions/{nupay_subscription_id}/cancel"

        try:
            logger.info(f"Cancelando assinatura: {nupay_subscription_id}")

            response = requests.post(
                url,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()
            logger.info(f"Assinatura cancelada com sucesso")

            return result

        except requests.exceptions.HTTPError as e:
            error_msg = f"Erro ao cancelar assinatura: {e.response.status_code}"
            logger.error(error_msg)
            raise NuPayError(error_msg)

        except requests.exceptions.RequestException as e:
            error_msg = f"Erro de conexão ao cancelar: {str(e)}"
            logger.error(error_msg)
            raise NuPayError(error_msg)

    def pause_subscription(self, nupay_subscription_id: str) -> Dict:
        """
        Pausa uma assinatura recorrente temporariamente.

        Args:
            nupay_subscription_id: ID da assinatura na NuPay

        Returns:
            dict com status da pausa
        """
        url = f"{self.base_url}/v1/subscriptions/{nupay_subscription_id}/pause"

        try:
            logger.info(f"Pausando assinatura: {nupay_subscription_id}")

            response = requests.post(
                url,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()

            return response.json()

        except requests.exceptions.HTTPError as e:
            error_msg = f"Erro ao pausar assinatura: {e.response.status_code}"
            logger.error(error_msg)
            raise NuPayError(error_msg)

        except requests.exceptions.RequestException as e:
            error_msg = f"Erro de conexão ao pausar: {str(e)}"
            logger.error(error_msg)
            raise NuPayError(error_msg)

    def resume_subscription(self, nupay_subscription_id: str) -> Dict:
        """
        Retoma uma assinatura pausada.

        Args:
            nupay_subscription_id: ID da assinatura na NuPay

        Returns:
            dict com status da retomada
        """
        url = f"{self.base_url}/v1/subscriptions/{nupay_subscription_id}/resume"

        try:
            logger.info(f"Retomando assinatura: {nupay_subscription_id}")

            response = requests.post(
                url,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()

            return response.json()

        except requests.exceptions.HTTPError as e:
            error_msg = f"Erro ao retomar assinatura: {e.response.status_code}"
            logger.error(error_msg)
            raise NuPayError(error_msg)

        except requests.exceptions.RequestException as e:
            error_msg = f"Erro de conexão ao retomar: {str(e)}"
            logger.error(error_msg)
            raise NuPayError(error_msg)

    def refund_payment(self, psp_reference_id: str, amount: Optional[float] = None) -> Dict:
        """
        Estorna um pagamento (total ou parcial).

        Args:
            psp_reference_id: ID do pagamento na NuPay
            amount: Valor a estornar (None = estorno total)

        Returns:
            dict com status do estorno
        """
        url = f"{self.base_url}/v1/checkouts/payments/{psp_reference_id}/refund"

        payload = {}
        if amount is not None:
            payload["amount"] = {
                "value": float(amount),
                "currency": "BRL"
            }

        try:
            logger.info(f"Estornando pagamento: {psp_reference_id}, valor: {amount or 'total'}")

            response = requests.post(
                url,
                headers=self.headers,
                json=payload if payload else None,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()
            logger.info(f"Estorno realizado com sucesso")

            return result

        except requests.exceptions.HTTPError as e:
            error_msg = f"Erro ao estornar pagamento: {e.response.status_code}"
            try:
                error_detail = e.response.json()
                error_msg += f" - {error_detail}"
            except:
                pass
            logger.error(error_msg)
            raise NuPayError(error_msg)

        except requests.exceptions.RequestException as e:
            error_msg = f"Erro de conexão ao estornar: {str(e)}"
            logger.error(error_msg)
            raise NuPayError(error_msg)

    def get_subscription_status(self, nupay_subscription_id: str) -> Dict:
        """
        Consulta status de uma assinatura recorrente.

        Args:
            nupay_subscription_id: ID da assinatura na NuPay

        Returns:
            dict com status atual da assinatura
        """
        url = f"{self.base_url}/v1/subscriptions/{nupay_subscription_id}"

        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()

            return response.json()

        except requests.exceptions.HTTPError as e:
            error_msg = f"Erro ao consultar assinatura: {e.response.status_code}"
            logger.error(error_msg)
            raise NuPayError(error_msg)

        except requests.exceptions.RequestException as e:
            error_msg = f"Erro de conexão: {str(e)}"
            logger.error(error_msg)
            raise NuPayError(error_msg)

    def _format_phone(self, phone: str) -> str:
        """
        Formata telefone para padrão internacional.
        Entrada: (11) 99999-9999 ou 11999999999
        Saída: 5511999999999
        """
        if not phone:
            return ""

        # Remover tudo que não é número
        phone = ''.join(filter(str.isdigit, phone))

        # Adicionar código do país se não tiver
        if not phone.startswith('55'):
            phone = '55' + phone

        return phone


class NuPayError(Exception):
    """Exceção para erros da API NuPay."""
    pass


# Nota: Diferente do megaapi, NuPayService não é singleton
# porque precisa do app context para acessar current_app.config
# Use: nupay = NuPayService() dentro de uma rota/função
