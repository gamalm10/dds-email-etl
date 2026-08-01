import jsPDF from 'jspdf';
import type { Report, RiskLanguage, PaymentTerm, LeadTime } from '@/types/report';

export async function exportReportPDF(report: Report, risks: RiskLanguage[], payments: PaymentTerm[], leads: LeadTime[]) {
  const doc = new jsPDF();
  let y = 20;

  const addText = (text: string, size = 12, isBold = false) => {
    doc.setFontSize(size);
    doc.setFont('helvetica', isBold ? 'bold' : 'normal');
    doc.text(text, 14, y);
    y += size * 0.5;
  };

  addText('DDS Report', 20, true);
  addText(`Report #${report.id} - ${report.subject}`, 14);
  addText(`Date: ${report.report_date}`, 11);
  addText(`Sender: ${report.sender}`, 11);
  addText(`Risk Score: ${report.risk_score}`, 11);
  y += 10;

  addText('Items', 14, true);
  report.items.slice(0, 20).forEach((item) => {
    addText(`${item.brand.brand_category} (${item.availability_status}) - ${item.vendor || ''}`, 10);
  });
  y += 10;

  addText('Insights', 14, true);
  report.insights.slice(0, 15).forEach((ins) => {
    addText(`[${ins.severity}] ${ins.description}`, 10);
  });
  y += 10;

  addText('Risks', 14, true);
  risks.slice(0, 20).forEach((r) => {
    addText(`[${r.category}] ${r.phrase} (score: ${r.severity_score})`, 10);
  });
  y += 10;

  addText('Payment Terms', 14, true);
  payments.forEach((p) => {
    addText(`${p.payment_method}: ${p.deposit_pct ? p.deposit_pct + '%' : ''} ${p.balance_pct ? p.balance_pct + '%' : ''} ${p.expected_date || ''}`, 10);
  });

  if (y > 260) doc.addPage();
  addText('Lead Times', 14, true);
  leads.forEach((l) => {
    addText(`${l.days} days - ${l.status}`, 10);
  });

  doc.save(`report-${report.id}.pdf`);
}

export async function exportReportExcel(report: Report, risks: RiskLanguage[]) {
  const XLSX = await import('exceljs');
  const wb = new XLSX.Workbook();

  // Sheet 1: Items
  const ws1 = wb.addWorksheet('Items');
  ws1.columns = [
    { header: 'Brand', key: 'brand', width: 30 },
    { header: 'Division', key: 'division', width: 15 },
    { header: 'Status', key: 'status', width: 12 },
    { header: 'Vendor', key: 'vendor', width: 20 },
    { header: 'Milestone', key: 'milestone', width: 30 },
    { header: 'Shipment', key: 'shipment', width: 25 },
    { header: 'Qty', key: 'qty', width: 15 },
    { header: 'Financial', key: 'financial', width: 20 },
  ];
  report.items.forEach((item) => {
    ws1.addRow({
      brand: item.brand.brand_category,
      division: item.brand.division,
      status: item.availability_status,
      vendor: item.vendor,
      milestone: item.milestone,
      shipment: item.shipment_bis,
      qty: item.quantity_text,
      financial: item.financial_text,
    });
  });

  // Sheet 2: Insights
  const ws2 = wb.addWorksheet('Insights');
  ws2.columns = [
    { header: 'Type', key: 'type', width: 20 },
    { header: 'Severity', key: 'severity', width: 12 },
    { header: 'Description', key: 'desc', width: 50 },
  ];
  report.insights.forEach((ins) => {
    ws2.addRow({ type: ins.insight_type, severity: ins.severity, desc: ins.description });
  });

  // Sheet 3: Risks
  const ws3 = wb.addWorksheet('Risks');
  ws3.columns = [
    { header: 'Category', key: 'category', width: 20 },
    { header: 'Phrase', key: 'phrase', width: 40 },
    { header: 'Score', key: 'score', width: 10 },
  ];
  risks.forEach((r) => {
    ws3.addRow({ category: r.category, phrase: r.phrase, score: r.severity_score });
  });

  const buffer = await wb.xlsx.writeBuffer();
  const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `report-${report.id}.xlsx`;
  a.click();
  URL.revokeObjectURL(url);
}
