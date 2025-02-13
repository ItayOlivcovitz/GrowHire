from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QTableWidget, QTableWidgetItem


class JobResultsTable(QGroupBox):
    """Table displaying job search results."""

    def __init__(self):
        super().__init__("📋 Job Search Results")
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # ✅ Table Setup
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels(["Job Title", "Company", "Score", "Job URL", "Job Description"])
        self.results_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.results_table)

        self.setLayout(layout)

    def update_results(self, job_results):
        """Updates the job search results in the table."""
        self.results_table.setRowCount(0)
        for row_index, job in enumerate(job_results):
            self.results_table.insertRow(row_index)
            self.results_table.setItem(row_index, 0, QTableWidgetItem(job.get("job_title", "N/A")))
            self.results_table.setItem(row_index, 1, QTableWidgetItem(job.get("company_name", "N/A")))
            self.results_table.setItem(row_index, 2, QTableWidgetItem(str(job.get("score", "N/A"))))
            self.results_table.setItem(row_index, 3, QTableWidgetItem(job.get("job_url", "N/A")))
            self.results_table.setItem(row_index, 4, QTableWidgetItem(job.get("job_description", "N/A")))
