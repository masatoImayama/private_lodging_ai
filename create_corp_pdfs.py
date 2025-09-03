from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib import colors
import os

def create_tenant_001_corp_doc():
    """テナント001: ABC株式会社の企業文書"""
    pdf_path = "tenant_001_corp_doc.pdf"
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        alignment=TA_CENTER,
        fontSize=18,
        spaceAfter=30
    )
    
    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['BodyText'],
        alignment=TA_JUSTIFY,
        fontSize=12,
        leading=18
    )
    
    story.append(Paragraph("ABC株式会社 業務規程書", title_style))
    story.append(Paragraph("2025年度版", styles['Heading3']))
    story.append(Spacer(1, 0.5*inch))
    
    # 第1章：組織概要
    story.append(Paragraph("第1章：組織概要", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(
        "ABC株式会社は1985年に設立された総合商社です。"
        "本社は東京都千代田区に位置し、従業員数は約5,000名です。"
        "主要事業は、エネルギー資源の輸入販売、食品流通事業、不動産開発の3つの柱で構成されています。"
        "年間売上高は3兆円を超え、国内外に50以上の拠点を展開しています。"
        "企業理念は『信頼と革新で社会に貢献する』であり、持続可能な社会の実現を目指しています。", 
        body_style
    ))
    story.append(PageBreak())
    
    # 第2章：人事制度
    story.append(Paragraph("第2章：人事制度", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(
        "当社の人事評価制度は年2回（6月・12月）実施されます。"
        "評価項目は、業績達成度（40%）、能力評価（30%）、行動評価（30%）で構成されています。"
        "昇進・昇格は原則として4月1日付けで実施され、管理職登用試験は年1回11月に行われます。"
        "賞与は夏季（6月）と冬季（12月）の年2回支給され、基本給の2〜6ヶ月分が標準です。"
        "定年は65歳ですが、希望者は70歳まで継続雇用が可能です。", 
        body_style
    ))
    
    # 給与テーブル
    data = [
        ['職級', '基本給範囲', '役職手当'],
        ['一般職', '20-35万円', 'なし'],
        ['主任', '30-45万円', '3万円'],
        ['課長', '45-65万円', '10万円'],
        ['部長', '65-85万円', '20万円'],
    ]
    table = Table(data, colWidths=[2*inch, 2*inch, 2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 14),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND',(0,1),(-1,-1),colors.beige),
        ('GRID',(0,0),(-1,-1),1,colors.black)
    ]))
    story.append(Spacer(1, 0.3*inch))
    story.append(table)
    story.append(PageBreak())
    
    # 第3章：コンプライアンス規程
    story.append(Paragraph("第3章：コンプライアンス規程", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(
        "ABC株式会社のコンプライアンス体制は、取締役会直属のコンプライアンス委員会が統括します。"
        "内部通報制度（ABCホットライン）は24時間365日受付可能で、通報者の秘密は厳守されます。"
        "贈収賄防止規程により、接待の上限は1人あたり1万円、年間累計5万円と定められています。"
        "インサイダー取引防止のため、自社株式の売買は事前申請制となっています。"
        "個人情報保護方針に基づき、年1回の研修受講が全従業員に義務付けられています。", 
        body_style
    ))
    
    doc.build(story)
    print(f"Created: {pdf_path}")
    return pdf_path

def create_tenant_002_corp_doc():
    """テナント002: XYZ工業株式会社の企業文書"""
    pdf_path = "tenant_002_corp_doc.pdf"
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        alignment=TA_CENTER,
        fontSize=18,
        spaceAfter=30
    )
    
    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['BodyText'],
        alignment=TA_JUSTIFY,
        fontSize=12,
        leading=18
    )
    
    story.append(Paragraph("XYZ工業株式会社 安全管理マニュアル", title_style))
    story.append(Paragraph("第15版（2025年1月改定）", styles['Heading3']))
    story.append(Spacer(1, 0.5*inch))
    
    # 第1章：会社概要
    story.append(Paragraph("第1章：会社概要", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(
        "XYZ工業株式会社は1962年創業の精密機械メーカーです。"
        "本社工場は愛知県豊田市にあり、従業員数は約2,800名です。"
        "主力製品は自動車部品、産業用ロボット、医療機器の3分野です。"
        "ISO9001、ISO14001、IATF16949の認証を取得しており、品質管理体制は業界トップクラスです。"
        "2024年度の売上高は1,500億円で、海外売上比率は45%に達しています。", 
        body_style
    ))
    story.append(PageBreak())
    
    # 第2章：安全管理体制
    story.append(Paragraph("第2章：安全管理体制", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(
        "XYZ工業の安全目標は『ゼロ災害の継続』です。"
        "各製造ラインには安全責任者を配置し、毎朝の安全朝礼を実施しています。"
        "KYT（危険予知トレーニング）は月2回、全従業員が参加必須です。"
        "労働災害が発生した場合は、24時間以内に原因分析と対策立案を完了させます。"
        "安全表彰制度により、無災害記録を達成した部署には報奨金が支給されます。", 
        body_style
    ))
    
    # 安全指標テーブル
    data = [
        ['年度', '労災件数', '度数率', '強度率'],
        ['2022年', '3件', '0.82', '0.03'],
        ['2023年', '2件', '0.54', '0.02'],
        ['2024年', '1件', '0.27', '0.01'],
        ['目標値', '0件', '0.00', '0.00'],
    ]
    table = Table(data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.darkblue),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 12),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND',(0,1),(-1,-2),colors.lightblue),
        ('BACKGROUND',(0,-1),(-1,-1),colors.yellow),
        ('GRID',(0,0),(-1,-1),1,colors.black)
    ]))
    story.append(Spacer(1, 0.3*inch))
    story.append(table)
    story.append(PageBreak())
    
    # 第3章：品質管理規程
    story.append(Paragraph("第3章：品質管理規程", styles['Heading2']))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(
        "XYZ工業の品質方針は『顧客満足度No.1の製品づくり』です。"
        "全製品は出荷前に100%検査を実施し、不良品率は0.01%以下を維持しています。"
        "品質改善活動（QCサークル）は全部署で月1回開催され、改善提案制度により優秀な提案には最大10万円の報奨金が支給されます。"
        "サプライヤー管理では、年2回の品質監査を実施し、評価結果に基づく改善指導を行っています。"
        "製品リコールが発生した場合の対応フローが整備されており、48時間以内に対策本部を設置します。", 
        body_style
    ))
    
    doc.build(story)
    print(f"Created: {pdf_path}")
    return pdf_path

if __name__ == "__main__":
    print("Creating corporate document PDFs...")
    print("=" * 50)
    
    create_tenant_001_corp_doc()
    create_tenant_002_corp_doc()
    
    print("\n✅ Corporate PDFs created successfully!")
    print("- tenant_001_corp_doc.pdf: ABC株式会社 業務規程書")
    print("- tenant_002_corp_doc.pdf: XYZ工業株式会社 安全管理マニュアル")