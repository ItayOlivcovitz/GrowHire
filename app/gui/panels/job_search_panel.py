from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QLabel, QLineEdit, QComboBox, QCheckBox, QHBoxLayout


class JobSearchPanel(QGroupBox):
    """Panel for job search filters."""

    def __init__(self, growhire_bot):
        super().__init__("Job Search")
        self.growhire_bot = growhire_bot
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)

        self.job_title_field = QLineEdit()
        self.job_title_field.setPlaceholderText("e.g. Software Engineer")
        layout.addWidget(QLabel("Job Title"))
        layout.addWidget(self.job_title_field)

        self.location_field = QLineEdit()
        self.location_field.setPlaceholderText("e.g. Israel")
        layout.addWidget(QLabel("Location"))
        layout.addWidget(self.location_field)

        self.ai_provider_dropdown = QComboBox()
        self.ai_provider_dropdown.addItems(["OpenAI", "Gemini", "ChatService"])
        self.ai_provider_dropdown.setCurrentIndex(0)
        layout.addWidget(QLabel("AI Provider"))
        layout.addWidget(self.ai_provider_dropdown)

        self.date_posted_dropdown = QComboBox()
        self.date_posted_dropdown.addItems(["Any Time", "Past 24 hours", "Past Week", "Past Month"])
        layout.addWidget(QLabel("Date Posted"))
        layout.addWidget(self.date_posted_dropdown)

        self.experience_level_dropdown = QComboBox()
        self.experience_level_dropdown.addItems(
            ["Any", "Internship", "Entry level", "Associate", "Mid-Senior level", "Director", "Executive"]
        )
        layout.addWidget(QLabel("Experience Level"))
        layout.addWidget(self.experience_level_dropdown)

        work_type_box = QGroupBox("Work Type")
        work_type_layout = QHBoxLayout()
        self.remote_hybrid = QCheckBox("Hybrid")
        self.remote_onsite = QCheckBox("On-site")
        self.remote_remote = QCheckBox("Remote")
        work_type_layout.addWidget(self.remote_hybrid)
        work_type_layout.addWidget(self.remote_onsite)
        work_type_layout.addWidget(self.remote_remote)
        work_type_box.setLayout(work_type_layout)
        layout.addWidget(work_type_box)

        self.easy_apply_checkbox = QCheckBox("Easy Apply only")
        layout.addWidget(self.easy_apply_checkbox)

        self.setLayout(layout)

    def get_filters(self):
        """Collects and returns the filter settings as a dictionary."""
        filters = {}
        filters["date_posted"] = self.date_posted_dropdown.currentText()
        filters["experience_level"] = self.experience_level_dropdown.currentText()
        
        work_types = []
        if self.remote_hybrid.isChecked():
            work_types.append("Hybrid")
        if self.remote_onsite.isChecked():
            work_types.append("On-site")
        if self.remote_remote.isChecked():
            work_types.append("Remote")
        filters["work_type"] = work_types
        
        filters["easy_apply"] = self.easy_apply_checkbox.isChecked()
        return filters
    
    def get_ai_provider(self):
        """
        Returns the selected AI provider as a lowercase string.
        
        Returns:
            str: "openai", "gemini", or "chatservice"
        """
        provider_map = {
            "OpenAI": "openai",
            "Gemini": "gemini",
            "ChatService": "chatservice"
        }
        selected_text = self.ai_provider_dropdown.currentText()
        return provider_map.get(selected_text, "openai")  # Default to openai if not found
