from bs4 import BeautifulSoup
import re

# def parse_job_page(html: str) -> dict:
#     """Parse Dice job detail page HTML and return structured job data."""
#     soup = BeautifulSoup(html, "lxml")
#
#     # --- Job Title ---
#     job_title = "Not Available"
#     summary_div = None  # define upfront
#
#     # Old method: <h1> tag
#     h1 = soup.find("h1")
#     if h1:
#         job_title = h1.text.strip()
#     else:
#         # New method: look in summary text for <b> job title pattern
#         summary_div = soup.find("div", class_=lambda x: x and "job-detail-description-module" in x)
#         if summary_div:
#             match = re.search(r"searching for a <b>(.*?)</b>", str(summary_div), re.IGNORECASE)
#             if match:
#                 job_title = match.group(1).strip()
#
#     # --- Company Name & Link ---
#     company_name = "Not Available"
#     company_link = "Not Available"
#     # try <a> first
#     company_a = soup.find("a", href=True)
#     if company_a:
#         company_name = company_a.text.strip()
#         company_link = company_a["href"].strip()
#     else:
#         # fallback: look for <li> or <p> containing company info
#         company_p = soup.find(string=re.compile(r"Company", re.IGNORECASE))
#         if company_p:
#             company_name = company_p.strip()
#
#     # --- Location ---
#     location = "Not Available"
#     # Old method: <li> containing comma
#     loc_li = soup.find("li", string=lambda x: x and "," in x)
#     if loc_li:
#         location = loc_li.text.strip()
#     else:
#         # New method: inside summary text, look for 'in <City, ST>'
#         if summary_div:
#             match = re.search(r"in\s+([A-Za-z ,]+)</b>", str(summary_div))
#             if match:
#                 location = match.group(1).strip()
#
#     # --- Posted Date ---
#     posted_date = "Not Available"
#     posted_li = soup.find("li", string=lambda x: x and "Posted" in x)
#     if posted_li:
#         posted_date = posted_li.text.strip()
#
#     # --- Job Overview ---
#     overview_details = get_job_overview(soup)
#
#     # --- Recruiter Info ---
#     recruiter_info = recruiter_details(soup)
#
#     # --- Merge all info ---
#     job_data = {
#         "Job Title": job_title,
#         "Company Name": company_name,
#         "Company Link": company_link,
#         "Location": location,
#         "Posted Date": posted_date,
#     }
#     job_data.update(overview_details)
#     job_data.update(recruiter_info)
#
#     return job_data

def parse_job_page(html: str) -> dict:
    """Parse Dice job detail page HTML and return structured job data."""
    soup = BeautifulSoup(html, "lxml")

    job_data = {}

    # Job Header Card
    header_card = find_header_card(soup)
    if not header_card:
        return {"error": "No job header card found"}

    # Extract structured data
    job_data.update(extract_company_info(header_card))
    job_data.update(extract_job_title(header_card))
    job_data.update(extract_location_posted(header_card))
    job_data.update(classify_all_badges(header_card))

    # Merge with existing functions
    job_data.update(get_job_overview(soup))
    job_data.update(recruiter_details(soup))

    return job_data


def find_header_card(soup) -> BeautifulSoup:
    """Find the main job header card container."""
    return soup.find("div", {"data-testid": "job-detail-header-card"})


def extract_company_info(header_card) -> dict:
    """Extract company name and link from header card."""
    company_link = header_card.find("a", href=True)
    return {
        "Company Name": company_link.get_text(strip=True) if company_link else "Not Available",
        "Company Link": company_link["href"] if company_link else "Not Available",
    }


def extract_job_title(header_card) -> dict:
    """Extract job title from h1 in header card."""
    h1 = header_card.find("h1")
    return {
        "Job Title": h1.get_text(strip=True) if h1 else "Not Available"
    }


def extract_location_posted(header_card) -> dict:
    """Extract location and posted date from metadata span."""
    location_span = header_card.find("span", class_=lambda x: x and "text-font-light" in x)
    if not location_span:
        return {"Location": "Not Available", "Posted Date": "Not Available"}

    span_text = location_span.get_text(strip=True)
    parts = [part.strip() for part in span_text.split("•")]

    return {
        "Location": parts[0] if parts else "Not Available",
        "Posted Date": parts[1] if len(parts) > 1 else "Not Available",
    }


def classify_all_badges(header_card) -> dict:
    """
    Classify ALL badges into specific categories. No data loss.

    Returns: Position Types, Work Arrangement, Pay Information, Other Badges
    """
    all_badges = header_card.find_all("div", class_="SeuiInfoBadge")

    position_types = []
    work_arrangement = []
    pay_info = []
    other_badges = []

    for badge in all_badges:
        badge_text = badge.get_text(strip=True)

        # Position Type classification
        if is_position_type(badge_text):
            position_types.append(badge_text)

        # Work Arrangement
        elif is_work_arrangement(badge_text):
            work_arrangement.append(badge_text)

        # Pay information
        elif is_pay_info(badge_text):
            pay_info.append(badge_text)

        # Everything else
        else:
            other_badges.append(badge_text)

    return {
        "Position Types": position_types if position_types else "Not Available",
        "Work Arrangement": work_arrangement if work_arrangement else "Not Available",
        "Pay Information": pay_info if pay_info else "Not Available",
        "Other Badges": other_badges if other_badges else "Not Available",
    }


def is_position_type(badge_text: str) -> bool:
    """Check if badge indicates position/employment type."""
    keywords = ["c2c", "corp to corp", "corp", "w2", "independent", "contract"]
    return any(keyword in badge_text.lower() for keyword in keywords)


def is_work_arrangement(badge_text: str) -> bool:
    """Check if badge indicates work arrangement/location."""
    keywords = ["on-site", "onsite", "hybrid", "remote", "days"]
    return any(keyword in badge_text.lower() for keyword in keywords)


def is_pay_info(badge_text: str) -> bool:
    """Check if badge contains pay/rate information."""
    return "$" in badge_text or any(keyword in badge_text.lower() for keyword in ["hr", "hour", "pay", "rate"])


def get_job_overview(soup):
    details = {}

    # --- Employment / Pay / Work Arrangement / Travel ---
    for container in soup.find_all("div", class_=lambda x: x and "job-overview_detailContainer" in x):
        for chip in container.find_all("div", class_=lambda x: x and "chip_chip" in x):
            text = chip.text.strip()
            if "Contract" in text:
                details["Employment Type"] = text
            elif "$" in text:
                details["Pay"] = text
            elif "Hybrid" in text or "days" in text:
                details["Work Arrangement"] = text
            elif "Travel" in text:
                details["Travel Requirements"] = text

    # --- Skills ---
    skills = []
    # New structure: <h3>Skills</h3> followed by <ul><li>...
    skills_h3 = soup.find("h3", string=lambda x: x and "Skills" in x)
    if skills_h3:
        ul = skills_h3.find_next_sibling("ul")
        if ul:
            for li in ul.find_all("li"):
                div = li.find("div", class_=lambda x: x and "font-medium" in x)
                if div:
                    skills.append(div.text.strip())
    details["Primary Skill Set"] = skills

    # --- Job Description ---
    job_desc = soup.find("div", class_=lambda x: x and "job-detail-description-module" in x)
    if job_desc:
        details["Job Description"] = job_desc.get_text(separator="\n").strip()
    else:
        details["Job Description"] = "Not Available"

    return details


def recruiter_details(soup) -> dict:
    """
    Extract recruiter information from the new Dice recruiter section.
    New structure: h4 for name, span for title/company, profile link.
    """
    # Find recruiter container (flex-col with rounded-3xl styling)
    recruiter_container = soup.find("div", class_=lambda x: x and "rounded-3xl" in x and "flex-1" in x)

    if not recruiter_container:
        return {
            "Recruiter Name": "Not Available",
            "Recruiter Title": "Not Available",
            "Recruiter Company": "Not Available",
            "Recruiter Profile Link": "Not Available"
        }

    # Recruiter name (h4 tag)
    name_h4 = recruiter_container.find("h4")
    recruiter_name = name_h4.get_text(strip=True) if name_h4 else "Not Available"

    # Recruiter title/company (span under name)
    title_span = recruiter_container.find("span", class_=lambda x: x and "text-sm" in x)
    recruiter_title = title_span.get_text(strip=True) if title_span else "Not Available"

    # Profile link (View Profile button)
    profile_link = recruiter_container.find("a", href=True, string=lambda x: x and "View Profile" in x)
    profile_url = profile_link["href"] if profile_link else "Not Available"

    return {
        "Recruiter Name": recruiter_name,  # "Subhash Chandra"
        "Recruiter Title": recruiter_title,  # "Recruitment Specialist @ Techridge, Inc."
        "Recruiter Company": extract_company_from_title(recruiter_title),
        "Recruiter Profile Link": profile_url
    }


def extract_company_from_title(title: str) -> str:
    """Extract company name from recruiter title like 'Role @ Company'."""
    if "@" in title and "Not Available" not in title:
        return title.split("@")[-1].strip()
    return title  # Fallback to full title if no @ symbol
