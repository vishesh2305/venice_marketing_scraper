"""
Excel Export Utilities
Creates professional Excel exports with multiple sheets and formatting
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import (
    Font, Fill, PatternFill, Border, Side, Alignment, NamedStyle
)
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.chart import BarChart, Reference, PieChart
import json


class ExcelExporter:
    """
    Professional Excel exporter for marketing data
    Creates formatted workbooks with multiple sheets
    """
    
    # Color scheme for lead categories
    COLORS = {
        "hot": "FF6B6B",     # Red
        "warm": "FFB347",    # Orange  
        "cold": "74B9FF",    # Blue
        "header": "2D3436",  # Dark gray
        "header_text": "FFFFFF",  # White
        "alt_row": "F5F6FA"  # Light gray
    }
    
    def __init__(self, output_dir: str = "./exports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self._create_styles()
        
    def _create_styles(self):
        """Create reusable styles"""
        # Header style
        self.header_font = Font(
            name='Calibri',
            size=11,
            bold=True,
            color=self.COLORS["header_text"]
        )
        self.header_fill = PatternFill(
            start_color=self.COLORS["header"],
            end_color=self.COLORS["header"],
            fill_type="solid"
        )
        
        # Data styles
        self.data_font = Font(name='Calibri', size=10)
        self.alt_fill = PatternFill(
            start_color=self.COLORS["alt_row"],
            end_color=self.COLORS["alt_row"],
            fill_type="solid"
        )
        
        # Lead category fills
        self.hot_fill = PatternFill(
            start_color=self.COLORS["hot"],
            end_color=self.COLORS["hot"],
            fill_type="solid"
        )
        self.warm_fill = PatternFill(
            start_color=self.COLORS["warm"],
            end_color=self.COLORS["warm"],
            fill_type="solid"
        )
        self.cold_fill = PatternFill(
            start_color=self.COLORS["cold"],
            end_color=self.COLORS["cold"],
            fill_type="solid"
        )
        
        # Border
        thin_border = Side(style='thin', color='CCCCCC')
        self.border = Border(
            left=thin_border,
            right=thin_border,
            top=thin_border,
            bottom=thin_border
        )
        
    def export(
        self,
        data: Dict[str, Any],
        filename: Optional[str] = None
    ) -> str:
        """
        Export scraped data to Excel workbook
        
        Args:
            data: Export data from ExportMasterAgent
            filename: Optional filename (auto-generated if not provided)
            
        Returns:
            Path to created Excel file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"marketing_leads_{timestamp}.xlsx"
            
        filepath = os.path.join(self.output_dir, filename)
        
        wb = Workbook()
        
        # Remove default sheet
        wb.remove(wb.active)
        
        # Create sheets
        self._create_all_leads_sheet(wb, data)
        self._create_hot_leads_sheet(wb, data)
        self._create_statistics_sheet(wb, data)
        self._create_segments_sheet(wb, data)
        
        wb.save(filepath)
        return filepath
    
    def _create_all_leads_sheet(self, wb: Workbook, data: Dict):
        """Create main sheet with all leads"""
        ws = wb.create_sheet("All Leads", 0)
        
        # Define columns
        columns = [
            ("Name", 25),
            ("Title", 30),
            ("Company", 25),
            ("Email", 35),
            ("Phone", 20),
            ("LinkedIn", 45),
            ("Bio", 50),
            ("Lead Score", 12),
            ("Category", 12),
            ("Source", 40),
            ("Date", 12)
        ]
        
        # Write headers
        for col, (header, width) in enumerate(columns, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = self.border
            ws.column_dimensions[get_column_letter(col)].width = width
            
        # Write data
        profiles = data.get("export_ready_data", [])
        for row, profile in enumerate(profiles, 2):
            values = [
                profile.get("name", ""),
                profile.get("title", ""),
                profile.get("company", ""),
                profile.get("email", ""),
                profile.get("phone", ""),
                profile.get("linkedin", ""),
                profile.get("bio", "")[:100] + "..." if len(profile.get("bio", "")) > 100 else profile.get("bio", ""),
                profile.get("lead_score", 0),
                profile.get("lead_category", ""),
                profile.get("source", ""),
                profile.get("scraped_date", "")
            ]
            
            for col, value in enumerate(values, 1):
                cell = ws.cell(row=row, column=col, value=value)
                cell.font = self.data_font
                cell.border = self.border
                cell.alignment = Alignment(vertical='center', wrap_text=(col == 7))
                
                # Alternate row colors
                if row % 2 == 0:
                    cell.fill = self.alt_fill
                    
                # Color code lead category
                if col == 9:  # Category column
                    category = str(value).lower()
                    if category == "hot":
                        cell.fill = self.hot_fill
                        cell.font = Font(name='Calibri', size=10, bold=True, color="FFFFFF")
                    elif category == "warm":
                        cell.fill = self.warm_fill
                    elif category == "cold":
                        cell.fill = self.cold_fill
                        
        # Freeze header row
        ws.freeze_panes = "A2"
        
        # Add filter
        if profiles:
            ws.auto_filter.ref = f"A1:K{len(profiles) + 1}"
            
    def _create_hot_leads_sheet(self, wb: Workbook, data: Dict):
        """Create sheet with only hot leads"""
        ws = wb.create_sheet("🔥 Hot Leads", 1)
        
        # Filter hot leads
        hot_profiles = [
            p for p in data.get("export_ready_data", [])
            if p.get("lead_category", "").lower() == "hot"
        ]
        
        # Same structure as all leads
        columns = [
            ("Name", 25),
            ("Title", 30),
            ("Company", 25),
            ("Email", 35),
            ("Lead Score", 12),
            ("Priority Action", 40)
        ]
        
        # Headers
        for col, (header, width) in enumerate(columns, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = self.header_font
            cell.fill = PatternFill(start_color="FF6B6B", end_color="FF6B6B", fill_type="solid")
            cell.alignment = Alignment(horizontal='center', vertical='center')
            ws.column_dimensions[get_column_letter(col)].width = width
            
        # Data
        for row, profile in enumerate(hot_profiles, 2):
            values = [
                profile.get("name", ""),
                profile.get("title", ""),
                profile.get("company", ""),
                profile.get("email", ""),
                profile.get("lead_score", 0),
                f"Connect within 24h - Score: {profile.get('lead_score', 0)}"
            ]
            
            for col, value in enumerate(values, 1):
                cell = ws.cell(row=row, column=col, value=value)
                cell.font = self.data_font
                cell.alignment = Alignment(vertical='center')
                
    def _create_statistics_sheet(self, wb: Workbook, data: Dict):
        """Create statistics and summary sheet"""
        ws = wb.create_sheet("📊 Statistics", 2)
        
        stats = data.get("statistics", {})
        
        # Title
        ws.merge_cells('A1:D1')
        title_cell = ws['A1']
        title_cell.value = "Marketing Scrape Statistics"
        title_cell.font = Font(name='Calibri', size=16, bold=True)
        title_cell.alignment = Alignment(horizontal='center')
        
        # Statistics table
        stat_data = [
            ("Total Profiles", stats.get("total_profiles", 0)),
            ("With Email", stats.get("with_email", 0)),
            ("With Phone", stats.get("with_phone", 0)),
            ("Hot Leads", stats.get("hot_leads_count", 0)),
            ("Average Lead Score", stats.get("average_lead_score", 0))
        ]
        
        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 15
        
        for row, (label, value) in enumerate(stat_data, 3):
            label_cell = ws.cell(row=row, column=1, value=label)
            label_cell.font = Font(name='Calibri', size=11, bold=True)
            
            value_cell = ws.cell(row=row, column=2, value=value)
            value_cell.font = Font(name='Calibri', size=11)
            value_cell.alignment = Alignment(horizontal='right')
            
        # Add simple bar chart
        if stats.get("total_profiles", 0) > 0:
            # Data for chart
            ws['D3'] = "Category"
            ws['E3'] = "Count"
            
            segments = data.get("segments", {})
            ws['D4'] = "Hot"
            ws['E4'] = len(segments.get("hot_leads", []))
            ws['D5'] = "Warm"
            ws['E5'] = len(segments.get("warm_leads", []))
            ws['D6'] = "Cold"
            ws['E6'] = len(segments.get("cold_leads", []))
            
            chart = BarChart()
            chart.type = "col"
            chart.style = 10
            chart.title = "Leads by Category"
            
            data_ref = Reference(ws, min_col=5, min_row=3, max_row=6)
            cats_ref = Reference(ws, min_col=4, min_row=4, max_row=6)
            
            chart.add_data(data_ref, titles_from_data=True)
            chart.set_categories(cats_ref)
            chart.shape = 4
            chart.width = 12
            chart.height = 8
            
            ws.add_chart(chart, "A10")
            
    def _create_segments_sheet(self, wb: Workbook, data: Dict):
        """Create segments breakdown sheet"""
        ws = wb.create_sheet("🎯 Segments", 3)
        
        segments = data.get("segments", {})
        
        # Hot leads column
        ws['A1'] = "🔥 Hot Leads"
        ws['A1'].font = Font(name='Calibri', size=12, bold=True, color="FFFFFF")
        ws['A1'].fill = PatternFill(start_color="FF6B6B", end_color="FF6B6B", fill_type="solid")
        
        for row, name in enumerate(segments.get("hot_leads", []), 2):
            ws.cell(row=row, column=1, value=name)
            
        # Warm leads column
        ws['B1'] = "🌡️ Warm Leads"
        ws['B1'].font = Font(name='Calibri', size=12, bold=True)
        ws['B1'].fill = PatternFill(start_color="FFB347", end_color="FFB347", fill_type="solid")
        
        for row, name in enumerate(segments.get("warm_leads", []), 2):
            ws.cell(row=row, column=2, value=name)
            
        # Cold leads column
        ws['C1'] = "❄️ Cold Leads"
        ws['C1'].font = Font(name='Calibri', size=12, bold=True, color="FFFFFF")
        ws['C1'].fill = PatternFill(start_color="74B9FF", end_color="74B9FF", fill_type="solid")
        
        for row, name in enumerate(segments.get("cold_leads", []), 2):
            ws.cell(row=row, column=3, value=name)
            
        # Decision makers column
        ws['D1'] = "👔 Decision Makers"
        ws['D1'].font = Font(name='Calibri', size=12, bold=True, color="FFFFFF")
        ws['D1'].fill = PatternFill(start_color="6C5CE7", end_color="6C5CE7", fill_type="solid")
        
        for row, name in enumerate(segments.get("decision_makers", []), 2):
            ws.cell(row=row, column=4, value=name)
            
        # Set column widths
        for col in ['A', 'B', 'C', 'D']:
            ws.column_dimensions[col].width = 30


def export_to_excel(data: Dict[str, Any], filename: Optional[str] = None) -> str:
    """
    Convenience function to export data to Excel
    """
    exporter = ExcelExporter()
    return exporter.export(data, filename)


def export_to_csv(data: Dict[str, Any], filename: Optional[str] = None) -> str:
    """
    Export data to CSV format
    """
    import csv
    
    output_dir = "./exports"
    os.makedirs(output_dir, exist_ok=True)
    
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"marketing_leads_{timestamp}.csv"
        
    filepath = os.path.join(output_dir, filename)
    
    profiles = data.get("export_ready_data", [])
    
    if not profiles:
        return filepath
        
    fieldnames = [
        "name", "title", "company", "email", "phone",
        "linkedin", "bio", "lead_score", "lead_category",
        "source", "scraped_date"
    ]
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(profiles)
        
    return filepath
