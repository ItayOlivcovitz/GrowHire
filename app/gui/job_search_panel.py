from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QLabel, QLineEdit, QComboBox, QCheckBox, QHBoxLayout


class JobSearchPanel(QGroupBox):
    """Panel for job search filters."""

    def __init__(self, growhire_bot):
        super().__init__("🔍 Job Search")
        self.growhire_bot = growhire_bot
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # ✅ Job Title Input
        self.job_title_field = QLineEdit()
        self.job_title_field.setPlaceholderText("Enter Job Title (Default: 'Software Engineer')")
        layout.addWidget(QLabel("🔹 Job Title:"))
        layout.addWidget(self.job_title_field)

        # ✅ Job Location Input
        self.location_field = QLineEdit()
        self.location_field.setPlaceholderText("Enter Job Location (Default: 'Israel')")
        layout.addWidget(QLabel("📍 Job Location:"))
        layout.addWidget(self.location_field)

        # ✅ Date Posted Dropdown
        self.date_posted_dropdown = QComboBox()
        self.date_posted_dropdown.addItems(["Any Time", "Past 24 hours", "Past Week", "Past Month"])
        layout.addWidget(QLabel("📅 Date Posted:"))
        layout.addWidget(self.date_posted_dropdown)

        # ✅ Experience Level Dropdown
        self.experience_level_dropdown = QComboBox()
        self.experience_level_dropdown.addItems(["Any", "Internship", "Entry level", "Associate", "Mid-Senior level", "Director", "Executive"])
        layout.addWidget(QLabel("💼 Experience Level:"))
        layout.addWidget(self.experience_level_dropdown)

        # ✅ Work Type
        work_type_box = QGroupBox("🖥️ Work Type")
        work_type_layout = QHBoxLayout()
        self.remote_hybrid = QCheckBox("Hybrid")
        self.remote_onsite = QCheckBox("On-site")
        self.remote_remote = QCheckBox("Remote")
        work_type_layout.addWidget(self.remote_hybrid)
        work_type_layout.addWidget(self.remote_onsite)
        work_type_layout.addWidget(self.remote_remote)
        work_type_box.setLayout(work_type_layout)
        layout.addWidget(work_type_box)

        # ✅ Easy Apply Checkbox
        self.easy_apply_checkbox = QCheckBox("⚡ Easy Apply Only")
        layout.addWidget(self.easy_apply_checkbox)

        self.setLayout(layout)
