import io
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer


def certificate_pdf(name,activity,organization,hours,code,emitted):
    output=io.BytesIO()
    doc=SimpleDocTemplate(output,pagesize=landscape(A4),rightMargin=60,leftMargin=60,topMargin=55,bottomMargin=40)
    title=ParagraphStyle('title',fontName='Helvetica-Bold',fontSize=30,leading=38,alignment=1,textColor=colors.HexColor('#166534'))
    text=ParagraphStyle('body',fontName='Helvetica',fontSize=16,leading=25,alignment=1)
    small=ParagraphStyle('small',parent=text,fontSize=10,leading=16)
    items=[Paragraph('VOLUNTIA',title),Spacer(1,24),Paragraph('Certificado de participación',title),Spacer(1,25),Paragraph(escape(name),text),Spacer(1,12),Paragraph('Participó en '+escape(activity),text),Paragraph(escape(organization),text),Spacer(1,12),Paragraph(f'{hours:.2f} horas de voluntariado',text),Spacer(1,30),Paragraph('Emisión: '+emitted.strftime('%d/%m/%Y'),small),Paragraph('Código de verificación: '+escape(code),small),Paragraph('Documento académico verificable en Voluntia. No equivale a una certificación profesional.',small)]
    doc.build(items)
    return output.getvalue()
