import os
import logging
from typing import Dict

import fitz  # PyMuPDF

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFService:
    def extract_form_fields(self, pdf_path: str) -> Dict[str, str]:
        """
        Extract form fields from a PDF
        Returns: Dict mapping field names to field types
        """
        try:
            doc = fitz.open(pdf_path)
            fields = {}
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Get form fields (widgets)
                for widget in page.widgets():
                    field_name = widget.field_name
                    field_type = self._get_field_type(widget.field_type)
                    
                    if field_name and field_name not in fields:
                        fields[field_name] = field_type
            
            doc.close()
            return fields
            
        except Exception as e:
            logger.error(f"Error extracting PDF fields: {str(e)}")
            raise Exception(f"Error extracting PDF fields: {str(e)}")
    
    def _get_field_type(self, widget_type: int) -> str:
        """
        Convert PyMuPDF widget type to readable string
        """
        type_mapping = {
            1: "text",        # PDF_WIDGET_TYPE_TEXT (old)
            2: "radiobutton", # PDF_WIDGET_TYPE_RADIOBUTTON  
            3: "combobox",    # PDF_WIDGET_TYPE_COMBOBOX (can also be checkbox)
            4: "listbox",     # PDF_WIDGET_TYPE_LISTBOX
            5: "signature",   # PDF_WIDGET_TYPE_SIGNATURE
            6: "unknown",     # PDF_WIDGET_TYPE_UNKNOWN
            7: "text",        # PDF_WIDGET_TYPE_TEXT (new in PyMuPDF 1.23+)
        }
        return type_mapping.get(widget_type, "text")
    
    def fill_pdf_form(self, input_path: str, field_values: Dict[str, str], session_id: str) -> str:
        """
        Fill PDF form with provided values and flatten the result for universal visibility
        Returns: Path to the filled PDF
        """
        try:
            doc = fitz.open(input_path)
            logger.info(f"Filling PDF: {input_path}")
            logger.info(f"Field values to set: {field_values}")
            
            # First pass: Fill all the form fields
            for page_num in range(len(doc)):
                page = doc[page_num]
                widgets = list(page.widgets())  # Convert generator to list
                logger.info(f"Page {page_num} widgets: {[w.field_name for w in widgets]}")
                
                for widget in widgets:
                    field_name = widget.field_name
                    logger.info(f"Widget: {field_name}, type: {widget.field_type}, value to set: {field_values.get(field_name)}")
                    if field_name in field_values:
                        value = field_values[field_name]
                        # Set field value based on type
                        if widget.field_type in [1, 7]:  # Text field (both old and new type codes)
                            widget.field_value = value
                            widget.update()
                        elif widget.field_type in [3]:  # Combobox (can be checkbox-like)
                            # Check if it's actually a checkbox by examining existing value
                            if hasattr(widget, 'choice_values') and widget.choice_values:
                                # It's a dropdown/combobox
                                widget.field_value = value
                            else:
                                # Treat as checkbox
                                is_checked = value.lower() in ["yes", "true", "1", "on", "checked"]
                                widget.field_value = is_checked
                            widget.update()
                        elif widget.field_type in [2]:  # Radio button
                            widget.field_value = value
                            widget.update()
                        elif widget.field_type in [4]:  # Listbox
                            widget.field_value = value
                            widget.update()
                        logger.info(f"Set value for {field_name}: {value}")
                    else:
                        logger.info(f"No value to set for {field_name}")

            # Second pass: Flatten the form by drawing text over fields and removing form interactivity
            for page_num in range(len(doc)):
                page = doc[page_num]
                widgets_to_process = list(page.widgets())  # Get current widgets
                
                for widget in widgets_to_process:
                    field_name = widget.field_name
                    value = field_values.get(field_name)
                    if value:
                        rect = widget.rect
                        logger.info(f"Flattening {field_name} at {rect}")
                        
                        # Draw text/symbols over the field area
                        if widget.field_type in [1, 7]:  # Text field
                            # Create a slightly smaller rect to avoid overlapping borders
                            text_rect = fitz.Rect(rect.x0 + 2, rect.y0 + 1, rect.x1 - 2, rect.y1 - 1)
                            page.insert_textbox(text_rect, str(value), fontsize=10, color=(0, 0, 0))
                        elif widget.field_type in [3]:  # Combobox/Checkbox
                            if hasattr(widget, 'choice_values') and widget.choice_values:
                                # It's a dropdown - show the selected value
                                text_rect = fitz.Rect(rect.x0 + 2, rect.y0 + 1, rect.x1 - 2, rect.y1 - 1)
                                page.insert_textbox(text_rect, str(value), fontsize=10, color=(0, 0, 0))
                            else:
                                # It's a checkbox - show checkmark if checked
                                if value.lower() in ["yes", "true", "1", "on", "checked"]:
                                    page.insert_textbox(rect, "✓", fontsize=12, color=(0, 0, 0), align=1)
                        elif widget.field_type in [2]:  # Radio button
                            if str(value).lower() not in ["no", "false", "0", "off", ""]:
                                # Draw a filled circle or dot for selected radio button
                                center_x = (rect.x0 + rect.x1) / 2
                                center_y = (rect.y0 + rect.y1) / 2
                                radius = min(rect.width, rect.height) / 4
                                page.draw_circle(fitz.Point(center_x, center_y), radius, color=(0, 0, 0), fill=(0, 0, 0))
                        elif widget.field_type in [4]:  # Listbox
                            text_rect = fitz.Rect(rect.x0 + 2, rect.y0 + 1, rect.x1 - 2, rect.y1 - 1)
                            page.insert_textbox(text_rect, str(value), fontsize=10, color=(0, 0, 0))

            # Remove all form fields to flatten the document
            # This needs to be done after drawing the content
            for page_num in range(len(doc)):
                page = doc[page_num]
                # Remove widgets by clearing the page's form fields
                page.clean_contents()  # Clean up any redundant content
                # Note: In PyMuPDF 1.23+, we need to remove annotations that represent form fields
                annots_to_remove = []
                for annot in page.annots():
                    if annot.type[0] == 2:  # Widget annotation (form field)
                        annots_to_remove.append(annot)
                
                for annot in annots_to_remove:
                    page.delete_annot(annot)

            # Save filled and flattened PDF
            upload_dir = os.getenv("UPLOAD_DIR", "uploads")
            output_path = os.path.join(upload_dir, f"{session_id}_filled.pdf")
            doc.save(output_path, incremental=False, deflate=True)
            doc.close()
            logger.info(f"Filled and flattened PDF saved to: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error filling PDF: {str(e)}")
            raise Exception(f"Error filling PDF: {str(e)}")
