# app/services/pdf_generator.py
"""
Gerador de PDF para extratos de comissao.

Utiliza ReportLab para gerar PDFs profissionais.
"""

import io
from datetime import datetime
from decimal import Decimal

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


class StatementPDFGenerator:
    """Gerador de PDF para extratos de colaboradores."""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Configura estilos personalizados."""
        self.styles.add(ParagraphStyle(
            name='TitleCustom',
            parent=self.styles['Title'],
            fontSize=18,
            spaceAfter=20,
            textColor=colors.HexColor('#2c3e50')
        ))

        self.styles.add(ParagraphStyle(
            name='SubtitleCustom',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#7f8c8d'),
            spaceAfter=10
        ))

        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#2980b9'),
            spaceBefore=15,
            spaceAfter=10
        ))

        self.styles.add(ParagraphStyle(
            name='RightAlign',
            parent=self.styles['Normal'],
            alignment=TA_RIGHT
        ))

        self.styles.add(ParagraphStyle(
            name='CenterAlign',
            parent=self.styles['Normal'],
            alignment=TA_CENTER
        ))

    def generate_statement_pdf(self, statement: dict) -> bytes:
        """
        Gera PDF do extrato de comissoes.

        Args:
            statement: Dict com dados do extrato (do SplitService.get_collaborator_statement)

        Returns:
            bytes do PDF gerado
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        elements = []

        # Cabecalho
        elements.append(Paragraph(
            "EXTRATO DE COMISSOES",
            self.styles['TitleCustom']
        ))

        elements.append(Paragraph(
            f"Periodo: {statement['period']['month']:02d}/{statement['period']['year']}",
            self.styles['SubtitleCustom']
        ))

        elements.append(Spacer(1, 10*mm))

        # Dados do Colaborador
        elements.append(Paragraph("DADOS DO COLABORADOR", self.styles['SectionHeader']))

        prof = statement['professional']
        prof_data = [
            ['Nome:', prof['name']],
            ['E-mail:', prof['email']],
            ['CPF:', prof.get('cpf', 'Nao informado')],
            ['Tipo:', prof.get('type', 'instructor').replace('_', ' ').title()]
        ]

        prof_table = Table(prof_data, colWidths=[4*cm, 12*cm])
        prof_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(prof_table)

        elements.append(Spacer(1, 10*mm))

        # Resumo Financeiro
        elements.append(Paragraph("RESUMO FINANCEIRO", self.styles['SectionHeader']))

        summary = statement['summary']
        summary_data = [
            ['Descricao', 'Valor'],
            ['Total de Atendimentos', str(summary['total_entries'])],
            ['Valor Bruto dos Creditos', f"R$ {summary['total_gross']:.2f}"],
            ['Taxa Academia', f"R$ {summary['total_academy']:.2f}"],
            ['VALOR LIQUIDO A RECEBER', f"R$ {summary['total_professional']:.2f}"],
        ]

        summary_table = Table(summary_data, colWidths=[10*cm, 6*cm])
        summary_table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2980b9')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            # Body
            ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            # Total row
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#27ae60')),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 11),
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
        ]))
        elements.append(summary_table)

        elements.append(Spacer(1, 10*mm))

        # Detalhamento
        elements.append(Paragraph("DETALHAMENTO", self.styles['SectionHeader']))

        if statement['entries']:
            # Header da tabela
            detail_data = [
                ['Data', 'Horario', 'Cliente', 'Modalidade', 'Status', 'Bruto', 'Split', 'Liquido']
            ]

            # Linhas
            for e in statement['entries']:
                date_str = e['date'].strftime('%d/%m') if e['date'] else '-'
                time_str = e['time'].strftime('%H:%M') if e['time'] else '-'

                # Truncar nome do cliente se muito longo
                client = e['client_name'][:15] + '...' if len(e['client_name']) > 18 else e['client_name']

                # Truncar modalidade
                modality = e['modality'][:10] + '...' if len(e['modality']) > 13 else e['modality']

                status = 'OK' if e['status'] == 'COMPLETED' else 'NS'

                detail_data.append([
                    date_str,
                    time_str,
                    client,
                    modality,
                    status,
                    f"R${e['credit_value']:.2f}",
                    f"{int(e['split_pct'])}%",
                    f"R${e['amount']:.2f}"
                ])

            # Linha de total
            detail_data.append([
                '', '', '', '', 'TOTAL',
                f"R${summary['total_gross']:.2f}",
                '',
                f"R${summary['total_professional']:.2f}"
            ])

            detail_table = Table(
                detail_data,
                colWidths=[1.8*cm, 1.5*cm, 3.5*cm, 2.5*cm, 1.2*cm, 2*cm, 1.3*cm, 2.2*cm]
            )
            detail_table.setStyle(TableStyle([
                # Header
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                # Body
                ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ALIGN', (5, 1), (-1, -1), 'RIGHT'),
                ('ALIGN', (4, 1), (4, -1), 'CENTER'),
                # Total row
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ecf0f1')),
                # Alternating rows
                ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f8f9fa')]),
                # Grid
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#bdc3c7')),
                # Padding
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
            ]))
            elements.append(detail_table)
        else:
            elements.append(Paragraph(
                "Nenhuma comissao registrada neste periodo.",
                self.styles['CenterAlign']
            ))

        elements.append(Spacer(1, 15*mm))

        # Rodape
        elements.append(Paragraph(
            f"Documento gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            self.styles['CenterAlign']
        ))

        elements.append(Paragraph(
            "Este documento e valido como comprovante de comissoes.",
            self.styles['CenterAlign']
        ))

        # Build PDF
        doc.build(elements)

        pdf_bytes = buffer.getvalue()
        buffer.close()

        return pdf_bytes


# Instancia global
pdf_generator = StatementPDFGenerator()
