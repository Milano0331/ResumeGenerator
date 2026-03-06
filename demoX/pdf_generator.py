from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import cm
import os
import sys
import re

def register_font():
    """Register the Chinese font (SimHei)."""
    
    # List of possible font paths
    font_paths = [
        # 1. Local directory (for development)
        os.path.abspath("simhei.ttf"),
        # 2. PyInstaller temporary directory (sys._MEIPASS)
        os.path.join(getattr(sys, '_MEIPASS', ''), 'simhei.ttf'),
        # 3. Windows system font directory
        "C:\\Windows\\Fonts\\simhei.ttf",
        "C:\\Windows\\Fonts\\msyh.ttf", # Microsoft YaHei as fallback
        "C:\\Windows\\Fonts\\simsun.ttc" # SimSun as fallback
    ]

    found_font = None
    font_name = 'SimHei'

    for path in font_paths:
        if path and os.path.exists(path):
            found_font = path
            break
            
    if not found_font:
        print("Warning: Chinese font (SimHei/Microsoft YaHei/SimSun) not found. Chinese characters may not display correctly.")
        return False
            
    try:
        # If it's a TTC (TrueType Collection), we need to pick an index, but reportlab TTFont usually handles TTF.
        # For simplicity, we prioritize TTF. If it's simsun.ttc, reportlab might need TrueTypeFont or different handling.
        # Let's stick to TTFont and hope for SimHei/YaHei first.
        pdfmetrics.registerFont(TTFont('SimHei', found_font))
        pdfmetrics.registerFont(TTFont('SimHei-Bold', found_font)) 
        return True
    except Exception as e:
        print(f"Error registering font '{found_font}': {e}")
        return False

def create_resume_pdf(markdown_content, output_file):
    """
    Convert markdown content to a PDF resume.
    """
    if not register_font():
        return

    # 1. Prepare Styles
    styles = getSampleStyleSheet()
    
    # Custom Styles
    style_normal = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName='SimHei',
        fontSize=10,
        leading=14,
        spaceAfter=4
    )
    
    style_h1 = ParagraphStyle(
        'CustomH1',
        parent=styles['Heading1'],
        fontName='SimHei',
        fontSize=18,
        leading=22,
        spaceAfter=6,
        textColor=colors.black
    )
    
    style_h2 = ParagraphStyle(
        'CustomH2',
        parent=styles['Heading2'],
        fontName='SimHei',
        fontSize=14,
        leading=18,
        spaceBefore=12,
        spaceAfter=6,
        textColor=colors.black,
        borderPadding=(2, 0, 2, 5), # Top, Right, Bottom, Left
        borderColor=colors.black,
        borderWidth=0,
        backColor=colors.Color(0.95, 0.95, 0.95), # Light gray background
    )

    style_contact = ParagraphStyle(
        'Contact',
        parent=styles['Normal'],
        fontName='SimHei',
        fontSize=9,
        leading=12,
        textColor=colors.darkgray
    )

    style_bullet = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        fontName='SimHei',
        fontSize=10,
        leading=14,
        leftIndent=20,
        firstLineIndent=0,
        spaceAfter=2
    )

    # 2. Parse Content
    lines = markdown_content.split('\n')
    
    # Basic parsing (assuming the generated format)
    # Line 0: Name (e.g., "# Name")
    # Line 2: Contact
    # This is brittle if the LLM output changes format, but we'll try to be robust.
    
    name_line = "Resume"
    contact_line = ""
    start_index = 0
    
    if len(lines) > 0:
        name_line = lines[0].strip().replace('# ', '').replace('#', '')
        start_index += 1
    
    # Try to find contact info (often lines 1-3)
    for i in range(1, min(5, len(lines))):
        line = lines[i].strip()
        if line and not line.startswith('#') and not line.startswith('-'):
            contact_line = line
            start_index = i + 1
            break

    # 3. Build Story
    story = []

    # --- Header Section (Table for Name/Contact + Photo) ---
    header_left = [
        Paragraph(name_line, style_h1),
        Spacer(1, 4),
        Paragraph(contact_line, style_contact)
    ]
    
    photo_text = Paragraph("<br/><br/>Photo<br/>(Optional)", style_normal)
    photo_table = Table([[photo_text]], colWidths=[2.5*cm], rowHeights=[3.5*cm])
    photo_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.gray),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,0), (-1,-1), colors.whitesmoke),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.gray),
    ]))

    header_data = [[header_left, photo_table]]
    t_header = Table(header_data, colWidths=[13*cm, 3*cm])
    t_header.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    
    story.append(t_header)
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("_" * 85, style_normal)) 
    story.append(Spacer(1, 0.5*cm))

    # --- Body Content ---
    for line in lines[start_index:]:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('## '):
            text = line.replace('## ', '')
            story.append(Paragraph(text, style_h2))
        elif line.startswith('### '):
             text = line.replace('### ', '')
             story.append(Paragraph(text, style_h2)) # Treat h3 similar to h2 for now
        elif line.startswith('---'):
            story.append(Spacer(1, 0.2*cm))
            story.append(Paragraph("_" * 85, style_normal))
            story.append(Spacer(1, 0.2*cm))
        elif line.startswith('- ') or line.startswith('* '):
            text = line[2:]
            text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
            text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
            story.append(Paragraph(f"• {text}", style_bullet))
        else:
            text = line
            text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
            text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
            if line.startswith('**'):
                 story.append(Paragraph(text, style_normal))
            else:
                 story.append(Paragraph(text, style_normal))

    # 4. Build PDF
    try:
        doc = SimpleDocTemplate(
            output_file,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        doc.build(story)
        print(f"Successfully generated PDF: {output_file}")
        return True
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return False
