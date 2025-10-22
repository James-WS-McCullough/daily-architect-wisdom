#!/usr/bin/env python3
"""
Fetch and parse all 97 articles from "97 Things Every Software Architect Should Know"
"""

import json
import re
import time
from urllib.request import urlopen, Request
from html.parser import HTMLParser
from typing import List, Dict

class ArticleParser(HTMLParser):
    """Parse HTML article to extract title, author, and content."""

    def __init__(self):
        super().__init__()
        self.title = ""
        self.author = ""
        self.content_parts = []
        self.in_h1 = False
        self.in_h2 = False
        self.in_h3 = False
        self.in_h4 = False
        self.in_h5 = False
        self.in_h6 = False
        self.in_p = False
        self.in_article = False
        self.in_footer = False
        self.in_author_p = False
        self.in_em = False
        self.in_i = False
        self.in_strong = False
        self.in_b = False
        self.in_ul = False
        self.in_ol = False
        self.in_li = False
        self.in_dl = False
        self.in_dt = False
        self.in_dd = False
        self.list_items = []
        self.ol_counter = 0
        self.current_text = ""
        self.current_p_class = None

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag == 'h1':
            self.in_h1 = True
        elif tag == 'h2':
            self.in_h2 = True
        elif tag == 'h3':
            self.in_h3 = True
        elif tag == 'h4':
            self.in_h4 = True
        elif tag == 'h5':
            self.in_h5 = True
        elif tag == 'h6':
            self.in_h6 = True
        elif tag == 'p':
            self.in_p = True
            self.current_p_class = attrs_dict.get('class', None)
            if self.current_p_class == 'author':
                self.in_author_p = True
        elif tag == 'article':
            self.in_article = True
        elif tag == 'footer':
            # Before entering footer, save any pending content
            if self.current_text.strip():
                if self.in_p and not self.in_author_p:
                    self.content_parts.append(self.current_text.strip())
                elif self.in_dd:
                    self.content_parts.append(self.current_text.strip())
                elif self.in_dt:
                    self.content_parts.append(f"**{self.current_text.strip()}**")
                self.current_text = ""
            self.in_footer = True
        elif tag == 'ul':
            self.in_ul = True
            self.list_items = []
        elif tag == 'ol':
            self.in_ol = True
            self.ol_counter = 0
            self.list_items = []
        elif tag == 'li':
            self.in_li = True
            self.current_text = ""
        elif tag == 'dl':
            self.in_dl = True
            self.list_items = []
        elif tag == 'dt':
            self.in_dt = True
            self.current_text = ""
        elif tag == 'dd':
            self.in_dd = True
            self.current_text = ""
        elif tag in ('em', 'i'):
            if (self.in_p or self.in_li or self.in_dt or self.in_dd or (self.in_h2 and self.title) or self.in_h3 or self.in_h4 or self.in_h5 or self.in_h6) and not self.in_author_p:
                # Add space before asterisk if previous char isn't already whitespace
                if self.current_text and not self.current_text[-1].isspace():
                    self.current_text += ' '
                self.current_text += '*'
            self.in_em = True if tag == 'em' else False
            self.in_i = True if tag == 'i' else False
        elif tag in ('strong', 'b'):
            # Don't add ** in dt tags since dt is already formatted as bold
            if (self.in_p or self.in_li or self.in_dd or (self.in_h2 and self.title) or self.in_h3 or self.in_h4 or self.in_h5 or self.in_h6) and not self.in_author_p and not self.in_dt:
                # Add space before double asterisk if previous char isn't already whitespace
                if self.current_text and not self.current_text[-1].isspace():
                    self.current_text += ' '
                self.current_text += '**'
            self.in_strong = True if tag == 'strong' else False
            self.in_b = True if tag == 'b' else False

    def handle_endtag(self, tag):
        if tag == 'h1':
            self.in_h1 = False
        elif tag == 'h2':
            self.in_h2 = False
            # If we already have a title, treat h2 as a content heading
            if self.title and self.current_text.strip() and not self.in_footer:
                self.content_parts.append(f"**{self.current_text.strip()}**")
                self.current_text = ""
        elif tag == 'h3':
            self.in_h3 = False
            # Add h3 content as a formatted heading
            if self.current_text.strip() and not self.in_footer:
                self.content_parts.append(f"**{self.current_text.strip()}**")
            self.current_text = ""
        elif tag == 'h4':
            self.in_h4 = False
            # Add h4 content as a formatted heading
            if self.current_text.strip() and not self.in_footer:
                self.content_parts.append(f"**{self.current_text.strip()}**")
            self.current_text = ""
        elif tag == 'h5':
            self.in_h5 = False
            # Add h5 content as a formatted heading
            if self.current_text.strip() and not self.in_footer:
                self.content_parts.append(f"**{self.current_text.strip()}**")
            self.current_text = ""
        elif tag == 'h6':
            self.in_h6 = False
            # Add h6 content as a formatted heading
            if self.current_text.strip() and not self.in_footer:
                self.content_parts.append(f"**{self.current_text.strip()}**")
            self.current_text = ""
        elif tag == 'p':
            self.in_p = False
            # Only add to content if it's not an author paragraph and not in footer
            if self.current_text.strip() and not self.in_author_p and not self.in_footer:
                self.content_parts.append(self.current_text.strip())
            self.current_text = ""
            self.current_p_class = None
            self.in_author_p = False
        elif tag == 'article':
            self.in_article = False
        elif tag == 'footer':
            self.in_footer = False
        elif tag == 'li':
            self.in_li = False
            if self.current_text.strip() and not self.in_footer:
                # Add the list item with appropriate prefix
                if self.in_ol:
                    self.ol_counter += 1
                    self.list_items.append(f"{self.ol_counter}) {self.current_text.strip()}")
                else:  # unordered list
                    self.list_items.append(f"- {self.current_text.strip()}")
            self.current_text = ""
        elif tag == 'ul':
            self.in_ul = False
            if self.list_items:
                # Add all list items as a single content part
                self.content_parts.append("\n".join(self.list_items))
            self.list_items = []
        elif tag == 'ol':
            self.in_ol = False
            if self.list_items:
                # Add all list items as a single content part
                self.content_parts.append("\n".join(self.list_items))
            self.list_items = []
            self.ol_counter = 0
        elif tag == 'dt':
            self.in_dt = False
            if self.current_text.strip() and not self.in_footer:
                # Add dt as a bold heading
                self.content_parts.append(f"**{self.current_text.strip()}**")
            self.current_text = ""
        elif tag == 'dd':
            self.in_dd = False
            if self.current_text.strip() and not self.in_footer:
                # Add dd as regular content
                self.content_parts.append(self.current_text.strip())
            self.current_text = ""
        elif tag == 'dl':
            self.in_dl = False
        elif tag in ('em', 'i'):
            if (self.in_p or self.in_li or self.in_dt or self.in_dd or (self.in_h2 and self.title) or self.in_h3 or self.in_h4 or self.in_h5 or self.in_h6) and not self.in_author_p:
                self.current_text += '*'
                # Add space after asterisk if next operation will add non-whitespace
                # (We'll handle this by checking in handle_data)
            self.in_em = False
            self.in_i = False
        elif tag in ('strong', 'b'):
            # Don't add ** in dt tags since dt is already formatted as bold
            if (self.in_p or self.in_li or self.in_dd or (self.in_h2 and self.title) or self.in_h3 or self.in_h4 or self.in_h5 or self.in_h6) and not self.in_author_p and not self.in_dt:
                self.current_text += '**'
            self.in_strong = False
            self.in_b = False

    def handle_data(self, data):
        text = data.strip()
        if not text:
            # Still need to preserve spaces in paragraph, list item, heading, and definition list content
            if (self.in_p and not self.in_author_p) or self.in_li or self.in_dt or self.in_dd or (self.in_h2 and self.title) or self.in_h3 or self.in_h4 or self.in_h5 or self.in_h6:
                self.current_text += data
            return

        # Capture title (from h1)
        if self.in_h1 and not self.title:
            self.title = text

        # Capture subtitle/author (from h2) or treat as content heading if title already set
        elif self.in_h2:
            if not self.title:
                self.title = text
            elif not self.in_footer:
                # If title is already set, capture h2 content as part of content
                self.current_text += data

        # Capture author from <p class="author">
        elif self.in_author_p:
            if text.lower().startswith('by '):
                self.author = text[3:].strip()
            else:
                self.author = text

        # Capture content (from p tags, li tags, heading tags, or definition list tags not in footer)
        elif (self.in_p or self.in_li or self.in_dt or self.in_dd or (self.in_h2 and self.title) or self.in_h3 or self.in_h4 or self.in_h5 or self.in_h6) and not self.in_footer:
            # If we just closed an emphasis/strong tag and data doesn't start with space/punctuation,
            # add a space before the new text
            if self.current_text and self.current_text[-1] == '*' and data and not data[0].isspace() and data[0] not in '.,;:!?)]}':
                self.current_text += ' '
            self.current_text += data

    def get_content(self):
        """Return the full content with paragraphs separated by double newlines."""
        # First, clean up single line breaks within each paragraph
        cleaned_parts = []
        for part in self.content_parts:
            # Check if this is a list (contains lines starting with - or numbers)
            lines = part.split('\n')
            is_list = any(line.strip().startswith(('-', '1)', '2)', '3)', '4)', '5)', '6)', '7)', '8)', '9)')) for line in lines)

            if is_list:
                # For lists, preserve the line breaks between items but clean up within items
                cleaned_lines = []
                for line in lines:
                    # Don't remove line breaks in lists, just clean up spaces
                    cleaned_line = re.sub(r' +', ' ', line.strip())
                    if cleaned_line:
                        cleaned_lines.append(cleaned_line)
                cleaned = '\n'.join(cleaned_lines)
            else:
                # For regular paragraphs, replace single newlines with spaces
                cleaned = re.sub(r'(?<!\n)\n(?!\n)', ' ', part)
                # Clean up multiple spaces
                cleaned = re.sub(r' +', ' ', cleaned)
                cleaned = cleaned.strip()

            cleaned_parts.append(cleaned)

        content = "\n\n".join(cleaned_parts)

        # Clean up spacing INSIDE emphasis markers only
        # Fix: "* word *" -> "*word*" (remove space after opening *)
        content = re.sub(r'(\s)\*\s+', r'\1*', content)
        # Fix: "* word *" -> "*word*" (remove space before closing *)
        content = re.sub(r'\s+\*(\s|[.,;:!?)\]])', r'*\1', content)
        # Same for strong tags (**)
        content = re.sub(r'(\s)\*\*\s+', r'\1**', content)
        content = re.sub(r'\s+\*\*(\s|[.,;:!?)\]])', r'**\1', content)
        return content


def fetch_article(filename: str) -> Dict[str, str]:
    """Fetch and parse a single article."""
    base_url = "https://yoshi389111.github.io/kinokobooks/soft_en/"
    url = base_url + filename

    print(f"Fetching: {filename}")

    try:
        # Add headers to avoid being blocked
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(req, timeout=30) as response:
            html = response.read().decode('utf-8')

        # Parse the HTML
        parser = ArticleParser()
        parser.feed(html)

        # Extract title, author, and content
        title = parser.title
        author = parser.author
        content = parser.get_content()

        # Fallback: if parser didn't find content, try alternative extraction
        if not content:
            # Try to extract from article/div/body tags
            content = extract_text_fallback(html)

        # Clean up title - remove special characters encoding issues
        title = title.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')

        return {
            "title": title,
            "author": author,
            "content": content
        }

    except Exception as e:
        print(f"Error fetching {filename}: {e}")
        return {
            "title": f"Error: {filename}",
            "author": "Unknown",
            "content": f"Failed to fetch article: {e}"
        }


def extract_text_fallback(html: str) -> str:
    """Fallback method to extract text content from HTML."""
    # Remove script and style tags
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)

    # Extract paragraphs, headings, and lists
    paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', html, flags=re.DOTALL)
    h2_headings = re.findall(r'<h2[^>]*>(.*?)</h2>', html, flags=re.DOTALL | re.IGNORECASE)
    h3_headings = re.findall(r'<h3[^>]*>(.*?)</h3>', html, flags=re.DOTALL | re.IGNORECASE)
    h4_headings = re.findall(r'<h4[^>]*>(.*?)</h4>', html, flags=re.DOTALL | re.IGNORECASE)
    h5_headings = re.findall(r'<h5[^>]*>(.*?)</h5>', html, flags=re.DOTALL | re.IGNORECASE)
    h6_headings = re.findall(r'<h6[^>]*>(.*?)</h6>', html, flags=re.DOTALL | re.IGNORECASE)
    ul_lists = re.findall(r'<ul[^>]*>(.*?)</ul>', html, flags=re.DOTALL | re.IGNORECASE)
    ol_lists = re.findall(r'<ol[^>]*>(.*?)</ol>', html, flags=re.DOTALL | re.IGNORECASE)

    # Helper function to clean HTML content
    def clean_html_content(content):
        # Convert emphasis tags to markdown before removing other tags
        text = re.sub(r'(\S)<em[^>]*>', r'\1 *', content, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'</em>(\S)', r'* \1', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'(\s)<em[^>]*>', r'\1*', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'</em>(\s)', r'*\1', text, flags=re.DOTALL | re.IGNORECASE)
        # Handle i tags similarly
        text = re.sub(r'(\S)<i[^>]*>', r'\1 *', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'</i>(\S)', r'* \1', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'(\s)<i[^>]*>', r'\1*', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'</i>(\s)', r'*\1', text, flags=re.DOTALL | re.IGNORECASE)
        # Handle strong tags
        text = re.sub(r'(\S)<strong[^>]*>', r'\1 **', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'</strong>(\S)', r'** \1', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'(\s)<strong[^>]*>', r'\1**', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'</strong>(\s)', r'**\1', text, flags=re.DOTALL | re.IGNORECASE)
        # Handle b tags
        text = re.sub(r'(\S)<b[^>]*>', r'\1 **', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'</b>(\S)', r'** \1', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'(\s)<b[^>]*>', r'\1**', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'</b>(\s)', r'**\1', text, flags=re.DOTALL | re.IGNORECASE)
        # Remove remaining HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Decode HTML entities
        text = text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
        text = text.replace('&quot;', '"').replace('&#39;', "'")
        return text

    # Clean up HTML tags and entities
    text_parts = []

    # Process paragraphs
    for p in paragraphs:
        text = clean_html_content(p)
        # Clean up single line breaks within the paragraph (convert to spaces)
        text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
        # Clean up multiple spaces
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        if text:
            text_parts.append(text)

    # Process h2 headings (skip first one as it's likely the title)
    for idx, h in enumerate(h2_headings):
        if idx == 0:
            continue  # Skip first h2 (title)
        text = clean_html_content(h)
        text = re.sub(r'\s+', ' ', text).strip()
        if text:
            text_parts.append(f"**{text}**")

    # Process h3 headings
    for h in h3_headings:
        text = clean_html_content(h)
        text = re.sub(r'\s+', ' ', text).strip()
        if text:
            text_parts.append(f"**{text}**")

    # Process h4 headings
    for h in h4_headings:
        text = clean_html_content(h)
        text = re.sub(r'\s+', ' ', text).strip()
        if text:
            text_parts.append(f"**{text}**")

    # Process h5 headings
    for h in h5_headings:
        text = clean_html_content(h)
        text = re.sub(r'\s+', ' ', text).strip()
        if text:
            text_parts.append(f"**{text}**")

    # Process h6 headings
    for h in h6_headings:
        text = clean_html_content(h)
        text = re.sub(r'\s+', ' ', text).strip()
        if text:
            text_parts.append(f"**{text}**")

    # Process unordered lists
    for ul in ul_lists:
        items = re.findall(r'<li[^>]*>(.*?)</li>', ul, flags=re.DOTALL | re.IGNORECASE)
        list_items = []
        for item in items:
            item_text = clean_html_content(item)
            item_text = re.sub(r'\s+', ' ', item_text).strip()
            if item_text:
                list_items.append(f"- {item_text}")
        if list_items:
            text_parts.append('\n'.join(list_items))

    # Process ordered lists
    for ol in ol_lists:
        items = re.findall(r'<li[^>]*>(.*?)</li>', ol, flags=re.DOTALL | re.IGNORECASE)
        list_items = []
        for idx, item in enumerate(items, 1):
            item_text = clean_html_content(item)
            item_text = re.sub(r'\s+', ' ', item_text).strip()
            if item_text:
                list_items.append(f"{idx}) {item_text}")
        if list_items:
            text_parts.append('\n'.join(list_items))

    return "\n\n".join(text_parts)


def main():
    """Main function to fetch all articles."""

    # List of all 97 article filenames
    filenames = [
        "Dont_put_your_resume_ahead_of_the_requirements.htm",
        "Simplify_essential_complexity;_diminish_accidental_complexity.htm",
        "Chances_are_your_biggest_problem_isnt_technical.htm",
        "Communication_is_King;_Clarity_and_Leadership_its_humble_servants.htm",
        "Application_architecture_determines_application_performance.htm",
        "Seek_the_value_in_requested_capabilities.htm",
        "Stand_Up.htm",
        "Everything_will_ultimately_fail.htm",
        "Youre_negotiating_more_often_than_you_think..htm",
        "Quantify.htm",
        "One_line_of_working_code_is_worth_500_of_specification.htm",
        "There_is_no_one-size-fits-all_solution.htm",
        "Its_never_too_early_to_think_about_performance.htm",
        "Architecting_is_about_balancing.htm",
        "Commit-and-run_is_a_crime..htm",
        "There_Can_be_More_than_One.htm",
        "Business_Drives.htm",
        "Simplicity_before_generality,_use_before_reuse.htm",
        "Architects_must_be_hands_on.htm",
        "Continuously_Integrate.htm",
        "Avoid_Scheduling_Failures.htm",
        "Architectural_Tradeoffs.htm",
        "Database_as_a_Fortress.htm",
        "Use_uncertainty_as_a_driver.htm",
        "Warning,_problems_in_mirror_may_be_larger_than_they_appear.htm",
        "Reuse_is_about_people_and_education,_not_just_architecture.htm",
        "There_is_no_I_in_architecture.htm",
        "Get_the_1000ft_view.htm",
        "Try_before_choosing.htm",
        "Understand_The_Business_Domain.htm",
        "Programming_is_an_act_of_design.htm",
        "Give_developers_autonomy.htm",
        "Time_changes_everything.htm",
        "The_title_of_software_architect_has_only_lower-case_as_deal_with_it.htm",
        "Scope_is_the_enemy_of_success.htm",
        "Value_stewardship_over_showmanship.htm",
        "Software_architecture_has_ethical_consequences.htm",
        "Skyscrapers_arent_scalable.htm",
        "Heterogeneity_Wins.htm",
        "Its_all_about_performance.htm",
        "Engineer_in_the_white_spaces.htm",
        "Talk_the_Talk.htm",
        "Context_is_King.htm",
        "Dwarves,_Elves,_Wizards,_and_Kings.htm",
        "Learn_from_Architects_of_Buildings.htm",
        "Fight_repetition.htm",
        "Welcome_to_the_Real_World.htm",
        "Dont_Control,_but_Observe.htm",
        "Janus_the_Architect.htm",
        "Architects_focus_is_on_the_boundaries_and_interfaces.htm",
        "Empower_developers.htm",
        "Record_your_rationale.htm",
        "Challenge_assumptions_-_especially_your_own.htm",
        "Share_your_knowledge_and_experiences.htm",
        "Pattern_Pathology.htm",
        "Dont_Stretch_The_Architecture_Metaphors.htm",
        "Focus_on_Application_Support_and_Maintenance.htm",
        "Prepare_to_pick_two.htm",
        "Prefer_principles,_axioms_and_analogies_to_opinion_and_taste.htm",
        "Start_with_a_Walking_Skeleton.htm",
        "It_is_all_about_the_data.htm",
        "Make_sure_the_simple_stuff_is_simple.htm",
        "Before_anything,_an_architect_is_a_developer.htm",
        "The_ROI_variable.htm",
        "Your_system_is_legacy,_design_for_it..htm",
        "If_there_is_only_one_solution,_get_a_second_opinion.htm",
        "Understand_the_impact_of_change.htm",
        "You_have_to_understand_Hardware_too.htm",
        "Shortcuts_now_are_paid_back_with_interest_later.htm",
        "Perfect_is_the_Enemy_of_Good_Enough.htm",
        "Avoid_Good_Ideas.htm",
        "Great_content_creates_great_systems.htm",
        "The_Business_Vs._The_Angry_Architect.htm",
        "Stretch_key_dimensions_to_see_what_breaks.htm",
        "If_you_design_it,_you_should_be_able_to_code_it..htm",
        "A_rose_by_any_other_name_will_end_up_as_a_cabbage.htm",
        "Stable_problems_get_high_quality_solutions.htm",
        "It_Takes_Diligence.htm",
        "Take_responsibility_for_your_decisions.htm",
        "Dont_Be_Clever.htm",
        "Choose_your_weapons_carefully,_relinquish_them_reluctantly.htm",
        "Your_Customer_is_Not_Your_Customer.htm",
        "It_will_never_look_like_that.htm",
        "Choose_Frameworks_that_play_well_with_others.htm",
        "Make_a_strong_business_case.htm",
        "Control_the_data,_not_just_the_code.htm",
        "Pay_down_your_technical_debt.htm",
        "Dont_Be_a_Problem_Solver.htm",
        "Build_Systems_to_be_Zuhanden.htm",
        "Find_and_retain_passionate_problem_solvers.htm",
        "Software_doesnt_really_exist.htm",
        "Learn_a_new_language.htm",
        "You_cant_future-proof_solutions.htm",
        "The_User_Acceptance_Problem.htm",
        "The_Importance_of_Consomme.htm",
        "For_the_end-user,_the_interface_is_the_system.htm",
        "Great_software_is_not_built,_it_is_grown.htm"
    ]

    articles = []

    for i, filename in enumerate(filenames, 1):
        print(f"\n[{i}/97] Processing: {filename}")
        article = fetch_article(filename)
        articles.append(article)

        # Be polite to the server - small delay between requests
        if i < len(filenames):
            time.sleep(0.5)

    # Create the final JSON structure
    output = {
        "inspiration": articles
    }

    # Write to file
    output_path = "/Users/jamesmccullough/Documents/Github/daily-architect-wisdom/src/data/articles.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n\nSuccessfully parsed {len(articles)} articles!")
    print(f"Output written to: {output_path}")

    # Print summary
    print("\n=== Summary ===")
    for i, article in enumerate(articles[:5], 1):
        print(f"{i}. {article['title']} by {article['author']}")
    print(f"... and {len(articles) - 5} more articles")


if __name__ == "__main__":
    main()
