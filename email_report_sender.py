from datetime import datetime
from loguru import logger


class EmailReportSender:
    def __init__(self, sender, password, recipient):
        self.sender = sender
        self.password = password
        self.recipient = recipient

    def generate_and_send(self, report_file_name, links_list, execution_time, visited_urls_num, thread_num):
        email_body = self.generate_email_body(report_file_name, links_list, execution_time, visited_urls_num, thread_num)
        self.send_email_report('blc@blc.org', 'password', email_body)

    def send_email_report(self, email, password, report_text):
        import smtplib
        from email.mime.text import MIMEText

        msg = MIMEText(report_text)
        msg['Subject'] = "Broken Links Crawler Report"
        msg['From'] = self.sender
        msg['To'] = self.recipient

        with smtplib.SMTP('localhost', 1025) as server:  # For local testing
            # For real SMTP use:
            # server.starttls()
            # server.login(self.sender, self.password)
            server.send_message(msg)

        logger.debug("Email sent.")

    @staticmethod
    def generate_email_body(report_file_name, links_list, execution_time, visited_urls_num, thread_num):
        """
        Generates an email-ready plain text report for a crawler run,
        saves it to a file, and returns the report content as a string.

        Parameters:
            report_file_name (str): File to save the report content.
            links_list (List[Dict]): List of link info.
            execution_time (float): Time taken by crawler (seconds).
            visited_urls_num (int): Number of visited URLs.
            thread_num (int): Number of threads used.

        Returns:
            str: The full plain-text report as a string.
        """
        lines = ["Subject: Crawler Report", "", "Crawler Report", "=" * 60,
                 f"Generated at     : {datetime.utcnow().isoformat()}Z",
                 f"Execution Time   : {execution_time}", f"Visited URLs     : {visited_urls_num}",
                 f"Threads Used     : {thread_num}", "=" * 60, "", "Discovered Links:", "-" * 60]

        for i, link in enumerate(links_list, start=1):
            lines += [f"[{i}] URL        : {link.url}",
                      f"     Depth       : {link.depth}",
                      f"     Appeared In : {link.first_found_on}",
                      f"     Status      : {link.status.name.lower()}",
                      f"     Error       : {link.error}", "-" * 60]

        report_content = "\n".join(lines)

        # # Save to file
        # with open(report_file_name, 'w', encoding='utf-8') as f:
        #     f.write(report_content)
        #
        # print(f"Email report saved to: {report_file_name}")
        return report_content
