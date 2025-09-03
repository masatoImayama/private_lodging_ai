from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
import os

def create_tenant_001_pdf():
    pdf_path = "tenant_001_manual.pdf"
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    title_style = styles['Heading1']
    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['BodyText'],
        alignment=TA_JUSTIFY,
        fontSize=12,
        leading=18
    )
    
    story.append(Paragraph("社内システム運用マニュアル - テナント001専用", title_style))
    story.append(Spacer(1, 0.5*inch))
    
    story.append(Paragraph("第1章：ログイン手順", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(
        "社内システムへのログインは以下の手順で行います。"
        "まず、社内ポータルサイトにアクセスし、左上のログインボタンをクリックします。"
        "次に、社員番号とパスワードを入力し、二要素認証コードを入力してください。"
        "初回ログイン時は、パスワードの変更が必要です。"
        "パスワードは8文字以上で、大文字・小文字・数字を含む必要があります。", 
        body_style
    ))
    story.append(PageBreak())
    
    story.append(Paragraph("第2章：勤怠管理システムの使い方", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(
        "勤怠管理システムは毎日の出退勤時刻を記録する重要なシステムです。"
        "出勤時は必ず打刻ボタンを押してください。"
        "退勤時も同様に打刻が必要です。"
        "月末には必ず勤怠データの確認を行い、上長の承認を得てください。"
        "休暇申請は3営業日前までに申請フォームから行ってください。", 
        body_style
    ))
    story.append(PageBreak())
    
    story.append(Paragraph("第3章：経費精算の流れ", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(
        "経費精算は月次で行います。"
        "領収書は必ず原本を保管し、スキャンしたPDFをシステムにアップロードしてください。"
        "交通費は自動計算されますが、タクシー利用時は理由の記載が必要です。"
        "接待費は事前申請が必要で、参加者リストと目的を明記してください。"
        "精算締切は毎月25日です。", 
        body_style
    ))
    
    doc.build(story)
    print(f"Created: {pdf_path}")
    return pdf_path

def create_tenant_002_pdf():
    pdf_path = "tenant_002_products.pdf"
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    title_style = styles['Heading1']
    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['BodyText'],
        alignment=TA_JUSTIFY,
        fontSize=12,
        leading=18
    )
    
    story.append(Paragraph("製品カタログ2025 - テナント002限定", title_style))
    story.append(Spacer(1, 0.5*inch))
    
    story.append(Paragraph("カテゴリA：高性能サーバー製品", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(
        "弊社の最新サーバー製品ラインナップをご紹介します。"
        "ProServer X500は、最大128コアのCPUと2TBのメモリを搭載可能です。"
        "冗長電源とRAID構成により、99.999%の稼働率を実現しています。"
        "価格は500万円からで、保守サポートは5年間付属します。"
        "データセンター向けの特別仕様もご用意しています。", 
        body_style
    ))
    story.append(PageBreak())
    
    story.append(Paragraph("カテゴリB：ストレージソリューション", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(
        "大容量ストレージシステムのご案内です。"
        "CloudStorage Pro は最大10PBまで拡張可能なオブジェクトストレージです。"
        "S3互換APIを提供し、既存システムとの連携も容易です。"
        "自動バックアップ機能により、データの安全性を確保します。"
        "月額料金は使用容量に応じた従量課金制です。", 
        body_style
    ))
    story.append(PageBreak())
    
    story.append(Paragraph("カテゴリC：ネットワーク機器", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(
        "最新のネットワーク機器をラインナップしています。"
        "SmartSwitch 8000シリーズは、100Gbpsのスループットを実現。"
        "SDN対応により、柔軟なネットワーク構成が可能です。"
        "セキュリティ機能も充実しており、DDoS攻撃対策も標準装備。"
        "導入支援サービスも提供しています。", 
        body_style
    ))
    
    doc.build(story)
    print(f"Created: {pdf_path}")
    return pdf_path

if __name__ == "__main__":
    create_tenant_001_pdf()
    create_tenant_002_pdf()
    print("\nTest PDFs created successfully!")
    print("- tenant_001_manual.pdf: 社内システム運用マニュアル")
    print("- tenant_002_products.pdf: 製品カタログ")