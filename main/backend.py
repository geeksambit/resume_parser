import logging
import re
import tika
from tika import parser
import docx2txt
import pdfplumber
import streamlit as st
import spacy
from pathlib import Path
import phonenumbers
from datetime import date
from dateparser.search import search_dates
import pandas as pd
import json
import os

tika.initVM()


class resumeparse(object):
    objective = (
        "career goal",
        "objective",
        "career objective",
        "employment objective",
        "professional objective",
        "summary",
        "career summary",
        "professional summary",
        "summary of qualifications",
        # 'digital'
    )

    work_and_employment = (
        "employment history",
        "work history",
        "work experience",
        "relevant work experience",
        "working experience",
        "work experiences",
        "work information",
        "experience",
        "professional experience",
        "professional experiences" "professional background",
        "additional experience",
        "career related experience",
        "career history",
        "related experience",
        "programming experience",
        "freelance",
        "freelance experience",
        "army experience",
        "military experience",
        "military background",
        "business and related experience",
        "internship",
        "internship / work experience",
    )

    education_and_training = (
        "academic background",
        "academic experience",
        "academic profile",
        "academic qualifications",
        "programs",
        "qualifications",
        "education and professional qualifications",
        "education & professional qualifications",
        "related courses",
        "education",
        "EDUCATION",
        "academic studies",
        "education & qualification",
        "educational background",
        "educational qualifications",
        "educational training",
        "education and training",
        "training",
        "academic training",
        "professional training",
        "course project experience",
        "related course projects",
        "internship experience",
        "internships",
        "apprenticeships",
        "college activities",
        "special training",
    )

    skills_header = (
        "credentials",
        "areas of experience",
        "areas of expertise",
        "areas of knowledge",
        "skills",
        "soft skills",
        "other skills",
        "other abilities",
        "career related skills",
        "professional skills",
        "specialized skills",
        "technical skills",
        "computer skills",
        "personal skills",
        "libraries",
        "frameworks",
        "computer knowledge",
        "technical experience",
        "proficiencies",
        "programming languages",
        "competencies",
    )

    languages = (
        "languages",
        "language competencies and skills",
        "foreign languages",
        "languages known",
    )

    projects = ("projects", "personal projects", "academic projects")

    certificates = (
        "certifications",
        "certification",
        "courses",
        "certificates",
        "professional certifications",
    )

    misc = (
        "activities and honors",
        "activities",
        "affiliations",
        "professional affiliations",
        "associations",
        "professional associations",
        "memberships",
        "professional memberships",
        "athletic involvement",
        "community involvement",
        "refere",
        "civic activities",
        "extra-curricular activities",
        "extra curricular activities",
        "open source contributions",
        "co-curricular activities" "professional activities",
        "volunteer work",
        "volunteer experience",
        "additional information",
        "interests",
        "additional info",
    )

    hobbies = ("hobbies", "hobby")

    accomplishments = (
        "achievement",
        "licenses",
        "academic achievements",
        "awards and achievements",
        "presentations",
        "conference presentations",
        "conventions",
        "dissertations",
        "exhibits",
        "papers",
        "publications",
        "professional publications",
        "research",
        "research grants",
        "current research interests",
        "thesis",
    )

    other_univ = ("college", "institute", "school", "university", "iit")


def find_segment_indices(string_to_search, resume_segments, resume_indices):
    for i, line in enumerate(string_to_search):

        if line[0].islower():
            continue

        header = line.lower()

        if [o for o in resumeparse.objective if header.startswith(o)]:
            try:
                resume_segments["objective"][header]
            except:
                resume_indices.append(i)
                header = [o for o in resumeparse.objective if header.startswith(o)][0]
                resume_segments["objective"][header] = i
        elif [w for w in resumeparse.work_and_employment if header.startswith(w)]:
            try:
                resume_segments["work_and_employment"][header]
            except:
                resume_indices.append(i)
                header = [
                    w for w in resumeparse.work_and_employment if header.startswith(w)
                ][0]
                resume_segments["work_and_employment"][header] = i
        elif [e for e in resumeparse.education_and_training if header.startswith(e)]:
            try:
                resume_segments["education_and_training"][header]
            except:
                resume_indices.append(i)
                header = [
                    e
                    for e in resumeparse.education_and_training
                    if header.startswith(e)
                ][0]
                resume_segments["education_and_training"][header] = i
        elif [p for p in resumeparse.projects if header.startswith(p)]:
            try:
                resume_segments["projects"][header]
            except:
                resume_indices.append(i)
                header = [p for p in resumeparse.projects if header.startswith(p)][0]
                resume_segments["projects"][header] = i
        elif [s for s in resumeparse.skills_header if header.startswith(s)]:
            try:
                resume_segments["skills"][header]
            except:
                resume_indices.append(i)
                header = [s for s in resumeparse.skills_header if header.startswith(s)][
                    0
                ]
                resume_segments["skills"][header] = i
        elif [l for l in resumeparse.languages if header.startswith(l)]:
            try:
                resume_segments["languages"][header]
            except:
                resume_indices.append(i)
                header = [l for l in resumeparse.languages if header.startswith(l)][0]
                resume_segments["languages"][header] = i
        elif [m for m in resumeparse.misc if header.startswith(m)]:
            try:
                resume_segments["misc"][header]
            except:
                resume_indices.append(i)
                header = [m for m in resumeparse.misc if header.startswith(m)][0]
                resume_segments["misc"][header] = i
        elif [a for a in resumeparse.accomplishments if header.startswith(a)]:
            try:
                resume_segments["accomplishments"][header]
            except:
                resume_indices.append(i)
                header = [
                    a for a in resumeparse.accomplishments if header.startswith(a)
                ][0]
                resume_segments["accomplishments"][header] = i
        elif [c for c in resumeparse.certificates if header.startswith(c)]:
            try:
                resume_segments["certificates"][header]
            except:
                resume_indices.append(i)
                header = [c for c in resumeparse.certificates if header.startswith(c)][
                    0
                ]
                resume_segments["certificates"][header] = i
        elif [h for h in resumeparse.hobbies if header.startswith(h)]:
            try:
                resume_segments["hobbies"][header]
            except:
                resume_indices.append(i)
                header = [h for h in resumeparse.hobbies if header.startswith(h)][0]
                resume_segments["hobbies"][header] = i


def slice_segments(string_to_search, resume_segments, resume_indices):
    resume_segments["contact_info"] = string_to_search[: resume_indices[0]]

    for section, value in resume_segments.items():
        if section == "contact_info":
            continue

        for sub_section, start_idx in value.items():
            end_idx = len(string_to_search)
            if (resume_indices.index(start_idx) + 1) != len(resume_indices):
                end_idx = resume_indices[resume_indices.index(start_idx) + 1]

            resume_segments[section][sub_section] = string_to_search[start_idx:end_idx]


def segment(string_to_search):
    resume_segments = {
        "objective": {},
        "work_and_employment": {},
        "education_and_training": {},
        "projects": {},
        "skills": {},
        "languages": {},
        "accomplishments": {},
        "misc": {},
        "hobbies": {},
        "certificates": {},
    }

    resume_indices = []

    find_segment_indices(string_to_search, resume_segments, resume_indices)
    if len(resume_indices) != 0:
        slice_segments(string_to_search, resume_segments, resume_indices)
    else:
        resume_segments["contact_info"] = []
    return resume_segments


def convert_docx_to_txt(docx_file):
    """
    A utility function to convert a Microsoft docx files to raw text.
    This code is largely borrowed from existing solutions, and does not match the style of the rest of this repo.
    :param docx_file: docx file with gets uploaded by the user
    :type docx_file: InMemoryUploadedFile
    :return: The text contents of the docx file
    :rtype: str
    """
    try:
        text = parser.from_buffer(docx_file)["content"]
    except RuntimeError as e:
        logging.error("Error in tika installation:: " + str(e))
        logging.error("--------------------------")
        logging.error("Install java for better result ")
        text = docx2txt.process(docx_file)
    except Exception as e:
        logging.error("Error in docx file:: " + str(e))
        return [], " "
    try:
        clean_text = re.sub(r"\n+", "\n", text)
        clean_text = clean_text.replace("\r", "\n").replace(
            "\t", " "
        )  # Normalize text blob
        resume_lines = clean_text.splitlines()  # Split text blob into individual lines
        resume_lines = [
            re.sub(
                "\s+|\[bookmark: _GoBack]|\[image: ]|\[image: image1.jpg]|\[image: image1.png]\[Page]",
                " ",
                line.strip(),
            )
            for line in resume_lines
            if line.strip()
        ]  # Remove empty strings and whitespaces
        return resume_lines, text
    except Exception as e:
        logging.error("Error in docx file:: " + str(e))
        return [], " "


def convert_pdf_to_txt(pdf_file):
    """
    A utility function to convert a machine-readable PDF to raw text.
    This code is largely borrowed from existing solutions, and does not match the style of the rest of this repo.
    :param input_pdf_path: Path to the .pdf file which should be converted
    :type input_pdf_path: str
    :return: The text contents of the pdf
    :rtype: str
    """
    # try:
    # PDFMiner boilerplate
    # pdf = pdfplumber.open(pdf_file)
    # full_string= ""
    # for page in pdf.pages:
    #   full_string += page.extract_text() + "\n"
    # pdf.close()

    try:
        raw_text = parser.from_buffer(pdf_file)["content"]
    except RuntimeError as e:
        logging.error("Error in tika installation:: " + str(e))
        logging.error("--------------------------")
        logging.error("Install java for better result ")
        pdf = pdfplumber.open(pdf_file)
        raw_text = ""
        for page in pdf.pages:
            raw_text += page.extract_text() + "\n"
        pdf.close()
    except Exception as e:
        logging.error("Error in docx file:: " + str(e))
        return [], " "
    try:
        full_string = re.sub(r"\n+", "\n", raw_text)
        full_string = full_string.replace("\r", "\n")
        full_string = full_string.replace("\t", " ")

        # Remove awkward LaTeX bullet characters

        full_string = re.sub(r"\uf0b7", " ", full_string)
        full_string = re.sub(r"\(cid:\d{0,2}\)", " ", full_string)
        full_string = re.sub(r"• ", " ", full_string)

        # Split text blob into individual lines
        resume_lines = full_string.splitlines(True)

        # Remove empty strings and whitespaces
        resume_lines = [
            re.sub("\s+", " ", line.strip()) for line in resume_lines if line.strip()
        ]
        return resume_lines, raw_text

    except Exception as e:
        logging.error("Error in docx file:: " + str(e))
        return [], " "


def ner_model(text, path):
    model = spacy.load(path)
    doc = model(text)
    return doc


def file_to_txt(file, filename):
    if filename.endswith("docx") or filename.endswith("doc"):
        resume_lines, raw_text = convert_docx_to_txt(file)
    elif filename.endswith("pdf"):
        resume_lines, raw_text = convert_pdf_to_txt(file)
    elif filename.endswith("txt"):
        with open(file, "r", encoding="latin") as f:
            resume_lines = f.readlines()
    else:
        resume_lines = None
    resume_segments = segment(resume_lines)
    return resume_segments, resume_lines


def find_phone(text):
    try:
        return list(iter(phonenumbers.PhoneNumberMatcher(text, None)))[0].raw_string
    except:
        try:
            return re.search(
                r"(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4})",
                text,
            ).group()
        except:
            return ""


def extract_email(text):
    email = re.findall(r"\S+@\S+", text)
    if email:
        try:
            return email[0].split()[0].strip(";")
        except IndexError:
            return None


def extract_github(text):
    github = re.findall("github.com\S+", text)
    if github:
        for profile_link in github:
            link = profile_link.split("/")
            try:
                link.remove("https")
                link.remove("")
            except:
                pass
            if len(link) == 2:
                try:
                    return profile_link.split()[0].strip(";")
                except IndexError:
                    return None


def extract_linkedin(text):
    linkedin = re.findall("linkedin.com/in\S+", text)
    if linkedin:
        try:
            return linkedin[0].split()[0].strip(";")
        except IndexError:
            return None


def personal_details(resume_lines, resume_segments):

    full_text = " ".join(resume_lines)
    # text = "\n".join(resume_lines)
    # print(full_text)
    data_path = Path("data")
    model_path = Path("/home/sambit/awesome/resume_parser/main/model/ner model-2")
    email = extract_email(full_text)
    phone = find_phone(full_text)
    github = extract_github(full_text)
    linkedin = extract_linkedin(full_text)
    location = extract_location(
        " ".join(resume_segments["contact_info"]),
        os.path.join("/home/sambit/awesome/resume_parser/main/data", "worldcities.csv"),
    )
    dob = None
    doc = ner_model(full_text, model_path)
    name = []
    summary = []
    for ent in doc.ents:
        if ent.label_.upper() == "NAME":
            name.append(ent.text)
        elif ent.label_.upper() == "DOB":
            dob = ent.text
        elif ent.label_.upper() == "SUMMARY":
            summary.append(ent.text)
    if summary == []:
        for key in resume_segments["objective"].keys():
            summary.extend(resume_segments["objective"][key][1:])
    doc = ner_model(full_text, r"/home/sambit/awesome/resume_parser/main/model/ner model-3")
    name = []
    summary = []
    for ent in doc.ents:
        if ent.label_.upper() == "NAME":
            name.append(ent.text)
        elif ent.label_.upper() == "DOB":
            dob = ent.text
        elif ent.label_.upper() == "SUMMARY":
            summary.append(ent.text)
    if summary == []:
        for key in resume_segments["objective"].keys():
            summary.extend(resume_segments["objective"][key][1:])

    fullName = name[0] if len(name) > 0 else None
    if fullName is not None:
        nl = fullName.split(" ")
        firstName = " ".join(nl[:-1])
        lastName = " ".join(nl[-1:])
    else:
        firstName = None
        lastName = None
    if dob is not None:
        for i in search_dates(dob):
            dateob = str(i[1].date().strftime("%d-%m-%Y"))
    else:
        dateob = None
    return {
        "fullName": fullName,
        "firstName": firstName,
        "lastName": lastName,
        "email": email,
        "contactNumber": phone,
        "githubProfile": github,
        "linkedinProfile": linkedin,
        "careerObjective": " ".join(summary),
        "address": location[0] if len(location) > 0 else None,
        "dob": dateob,
    }


def extract_location(text, file):
    df = pd.read_csv(file, header=None)
    cities = [i.lower() for i in df[1]]
    location = []
    for i in range(len(cities)):

        if re.findall(r"\b" + cities[i] + r"\b", text.lower()):
            location.append(df[1][i] + ", " + df[4][i])
            break
    return location


def extract_passing_year(text_lines):
    listsearch = [t.lower() for t in text_lines]
    passing_year = []
    year = "(^19\d{2}|\s19\d{2}|^20\d{2}|\s20\d{2})"
    for i in range(len(listsearch)):
        if re.findall(year, listsearch[i]):
            if re.findall("present", listsearch[i]):
                passing_year.append(
                    str(re.findall(year, listsearch[i])[0]) + " Present"
                )
            elif len(re.findall(year, listsearch[i])) > 1:
                passing_year.append(
                    str(re.findall(year, listsearch[i])[0])
                    + " "
                    + str(re.findall(year, listsearch[i])[1])
                )
            else:
                passing_year.append(re.findall(year, listsearch[i])[0])
    return passing_year


def calculate_experience(resume_text):
    #
    # def get_month_index(month):
    #   month_dict = {'jan':1, 'feb':2, 'mar':3, 'apr':4, 'may':5, 'jun':6, 'jul':7, 'aug':8, 'sep':9, 'oct':10, 'nov':11, 'dec':12}
    #   return month_dict[month.lower()]

    def correct_year(result):
        if len(result) < 2:
            if int(result) > int(str(date.today().year)[-2:]):
                result = str(int(str(date.today().year)[:-2]) - 1) + result
            else:
                result = str(date.today().year)[:-2] + result
        return result

    # try:
    experience = 0
    start_month = -1
    start_year = -1
    end_month = -1
    end_year = -1
    exp_range = []
    not_alpha_numeric = r"[^a-zA-Z\d]"
    number = r"(\d{2})"

    months_num = r"(01)|(02)|(03)|(04)|(05)|(06)|(07)|(08)|(09)|(10)|(11)|(12)"
    months_short = (
        r"(jan)|(feb)|(mar)|(apr)|(may)|(jun)|(jul)|(aug)|(sep)|(oct)|(nov)|(dec)"
    )
    months_long = (
        r"(january)|(february)|(march)|(april)|(may)|(june)|(july)|(august)|(september)|(october)|("
        r"november)|(december) "
    )
    month = r"(" + months_num + r"|" + months_short + r"|" + months_long + r")"
    regex_year = r"((20|19)(\d{2})|(\d{2}))"
    year = regex_year
    start_date = month + not_alpha_numeric + r"?" + year

    end_date = (
        r"(("
        + number
        + r"?"
        + not_alpha_numeric
        + r"?"
        + month
        + not_alpha_numeric
        + r"?"
        + year
        + r")|(present|current)) "
    )
    longer_year = r"((20|19)(\d{2}))"
    year_range = (
        longer_year
        + r"("
        + not_alpha_numeric
        + r"{1,4}|(\s*to\s*))"
        + r"("
        + longer_year
        + r"|(present"
        r"|current)) "
    )
    date_range = (
        r"("
        + start_date
        + r"("
        + not_alpha_numeric
        + r"{1,4}|(\s*to\s*))"
        + end_date
        + r")|("
        + year_range
        + r")"
    )

    regular_expression = re.compile(date_range, re.IGNORECASE)
    punc = """!()[]{};'"\,<>?@#$%^&*_~\\"""
    for ele in resume_text:
        if ele in punc:
            resume_text = resume_text.replace(ele, " ")
    # print(resume_text)
    regex_result = re.search(regular_expression, resume_text)
    try:
        exp_range.append(regex_result.group())
        # print(regex_result.group())
    except:
        pass
    while regex_result:

        date_range = regex_result.group()
        try:
            year_range_find = re.compile(year_range, re.IGNORECASE)
            year_range_find = re.search(year_range_find, date_range)
            replace = re.compile(
                r"(" + not_alpha_numeric + r"{1,4}|(\s*to\s*))", re.IGNORECASE
            )
            replace = re.search(replace, year_range_find.group().strip())

            start_year_result, end_year_result = (
                year_range_find.group().strip().split(replace.group())
            )
            start_year_result = int(correct_year(start_year_result))
            if (
                end_year_result.lower().find("present") != -1
                or end_year_result.lower().find("current") != -1
                or end_year_result.lower().find("till date") != -1
            ):
                end_month = date.today().month  # current month
                end_year_result = date.today().year  # current year
            else:
                end_year_result = int(correct_year(end_year_result))

        except:

            start_date_find = re.compile(start_date, re.IGNORECASE)
            start_date_find = re.search(start_date_find, date_range)

            non_alpha = re.compile(not_alpha_numeric, re.IGNORECASE)
            non_alpha_find = re.search(non_alpha, start_date_find.group().strip())

            replace = re.compile(
                start_date + r"(" + not_alpha_numeric + r"{1,4}|(\s*to\s*))",
                re.IGNORECASE,
            )
            replace = re.search(replace, date_range)
            date_range = date_range[replace.end() :]

            start_year_result = (
                start_date_find.group().strip().split(non_alpha_find.group())[-1]
            )

            # if len(start_year_result)<2:
            #   if int(start_year_result) > int(str(date.today().year)[-2:]):
            #     start_year_result = str(int(str(date.today().year)[:-2]) - 1 )+start_year_result
            #   else:
            #     start_year_result = str(date.today().year)[:-2]+start_year_result
            # start_year_result = int(start_year_result)
            start_year_result = int(correct_year(start_year_result))

            if (
                date_range.lower().find("present") != -1
                or date_range.lower().find("current") != -1
            ):
                end_month = date.today().month  # current month
                end_year_result = date.today().year  # current year
            else:
                end_date_find = re.compile(end_date, re.IGNORECASE)
                end_date_find = re.search(end_date_find, date_range)

                end_year_result = (
                    end_date_find.group().strip().split(non_alpha_find.group())[-1]
                )

                # if len(end_year_result)<2:
                #   if int(end_year_result) > int(str(date.today().year)[-2:]):
                #     end_year_result = str(int(str(date.today().year)[:-2]) - 1 )+end_year_result
                #   else:
                #     end_year_result = str(date.today().year)[:-2]+end_year_result
                # end_year_result = int(end_year_result)
                end_year_result = int(correct_year(end_year_result))

        if (start_year == -1) or (start_year_result <= start_year):
            start_year = start_year_result
        if (end_year == -1) or (end_year_result >= end_year):
            end_year = end_year_result

        resume_text = resume_text[regex_result.end() :].strip()
        regex_result = re.search(regular_expression, resume_text)
        try:
            exp_range.append(regex_result.group())
        except:
            pass
    return end_year - start_year, exp_range  # Use the obtained month attribute


def get_experience(resume_segments, label="work"):
    total_exp = 0
    if len(resume_segments["work_and_employment"].keys()) and label == "work":
        text = ""
        for key, values in resume_segments["work_and_employment"].items():
            text += " ".join(values) + " "
        total_exp, exp_range = calculate_experience(text)
        return total_exp, exp_range
    if len(resume_segments["education_and_training"].keys()) and label == "education":
        text = ""
        for key, values in resume_segments["education_and_training"].items():
            text += " ".join(values) + " "
        total_exp, exp_range = calculate_experience(text)
        return total_exp, exp_range
    else:
        text = ""
        for key in resume_segments.keys():
            if key != "education_and_training":
                if key == "contact_info":
                    text += " ".join(resume_segments[key]) + " "
                else:
                    for key_inner, value in resume_segments[key].items():
                        text += " ".join(value) + " "
        total_exp, exp_range = calculate_experience(text)
        return total_exp, exp_range


def education_details(resume_lines, resume_segments):
    model_path = Path("/home/sambit/awesome/resume_parser/main/model/ner model-2")
    education_segment = []
    for key in resume_segments["education_and_training"].keys():
        education_segment.extend(resume_segments["education_and_training"][key][1:])
    education = []
    startDate = []
    endDate = []
    try:
        _, edu_duration = get_experience(resume_segments, label="education")
    except:
        edu_duration = None
    #    print(edu_duration)

    if edu_duration is not None and edu_duration != []:
        for i in edu_duration:
            date = search_dates(i)
            if date is not None and len(date) > 0:
                startDate.append(date[0][1].strftime("%m-%Y"))
                if (
                    "present" in i.lower()
                    or "current" in i.lower()
                    or "till date" in i.lower()
                ):
                    endDate.append("present")
                else:
                    endDate.append(date[1][1].strftime("%m-%Y"))
            else:
                i = re.sub("[^0-9a-zA-Z]+", " ", i)
                i = i.split()
                if len(i) == 2:
                    startDate.append(i[0])
                    if "present" in i or "current" in i or "till date" in i:
                        endDate.append("present")
                    else:
                        endDate.append(i[1])
                else:
                    startDate.append(None)
                    endDate.append(i[0])
    elif edu_duration is None or edu_duration == []:
        edu_duration = extract_passing_year(education_segment)
        if edu_duration:
            for entry in edu_duration:
                entry = entry.split()
                if len(entry) == 2:
                    startDate.append(entry[0])
                    if "present" in entry or "current" in entry or "till date" in entry:
                        endDate.append("present")
                    else:
                        endDate.append(entry[1])
                else:
                    startDate.append(None)
                    endDate.append(entry[0])
    #    print(resume_segments['education_and_training'])
    #    print(edu_duration)
    #    print(startDate, endDate)
    college = []
    degree = []
    doc = ner_model(" ".join(resume_lines), model_path)
    for ent in doc.ents:
        if ent.label_.upper() == "COLLEGE":
            college.append(ent.text)
        elif ent.label_.upper() == "DEGREE":
            degree.append(ent.text)

    col = college if len(college) > len(degree) else degree
    for i in range(len(col)):
        if edu_duration != []:
            try:
                if endDate[i] == "present":
                    education.append(
                        {
                            "university": college[i],
                            "degreeCertification": degree[i],
                            "startDate": startDate[i],
                            "endDate": endDate[i],
                            "currentlyActive": 1,
                        }
                    )
                else:
                    education.append(
                        {
                            "university": college[i],
                            "degreeCertification": degree[i],
                            "startDate": startDate[i],
                            "endDate": endDate[i],
                            "currentlyActive": 0,
                        }
                    )
            except:
                if i >= len(startDate):
                    try:
                        education.append(
                            {
                                "university": college[i],
                                "degreeCertification": degree[i],
                                "startDate": None,
                                "endDate": None,
                                "currentlyActive": 0,
                            }
                        )
                    except IndexError:
                        if col == college:
                            education.append(
                                {
                                    "university": college[i],
                                    "degreeCertification": None,
                                    "startDate": None,
                                    "endDate": None,
                                    "currentlyActive": 0,
                                }
                            )
                        else:
                            education.append(
                                {
                                    "university": None,
                                    "degreeCertification": degree[i],
                                    "startDate": None,
                                    "endDate": None,
                                    "currentlyActive": 0,
                                }
                            )
                else:
                    if col == college:
                        education.append(
                            {
                                "university": college[i],
                                "degreeCertification": None,
                                "startDate": startDate[i],
                                "endDate": endDate[i],
                                "currentlyActive": 0,
                            }
                        )
                    else:
                        education.append(
                            {
                                "university": None,
                                "degreeCertification": degree[i],
                                "startDate": startDate[i],
                                "endDate": endDate[i],
                                "currentlyActive": 0,
                            }
                        )
        else:
            try:
                education.append(
                    {
                        "university": college[i],
                        "degreeCertification": degree[i],
                        "startDate": None,
                        "endDate": None,
                        "currentlyActive": 0,
                    }
                )
            except:
                if col == college:
                    education.append(
                        {
                            "university": college[i],
                            "degreeCertification": None,
                            "startDate": None,
                            "endDate": None,
                            "currentlyActive": 0,
                        }
                    )
                else:
                    education.append(
                        {
                            "university": None,
                            "degreeCertification": degree[i],
                            "startDate": None,
                            "endDate": None,
                            "currentlyActive": 0,
                        }
                    )
    return education


def work_details(resume_lines, resume_segments):
    full_text = " ".join(resume_lines)
    # finder = find_job_titles.FinderAcora()
    model_path = Path("/home/sambit/awesome/resume_parser/main/model/ner model-2")
    data_path = Path("/home/sambit/awesome/resume_parser/main/data") 
    work_segment = []
    try:
        for key in resume_segments["work_and_employment"].keys():
            work_segment.extend(resume_segments["work_and_employment"][key][1:])
    except:
        return {}
    # print(work_segment)
    designation = []
    company = []
    doc = ner_model(full_text, model_path)  
    for ent in doc.ents:
        if ent.label_.upper() == "COMPANIES WORKED AT":
            company.append(ent.text)
        elif ent.label_.upper() == "DESIGNATION":
            designation.append(ent.text)

    #    print('work segment')
    #    for ent in doc.ents:
    #        print(f'{ent.label_.upper():{30}}- {ent.text}')
    #
    #    for i in range(len(work_segment)):
    #        try:
    #            job.append(finder.findall(work_segment[i])[0].match)
    #            company.append(work_segment[i+1])
    #        except:
    #            if re.findall('Intern',work_segment[i]):
    #                job.append(work_segment[i])
    #                company.append(work_segment[i+1])
    #    designition = job_designition(" ".join(work_segment))
    #    designition = list(dict.fromkeys(designition).keys())
    try:
        total_exp, exp_duration = get_experience(resume_segments)
    except:
        total_exp, exp_duration = None, None
    work_exp = []
    startDate = []
    endDate = []
    work = company if len(company) > len(designation) else designation
    # print(work)
    # print(exp_duration)
    if exp_duration is not None:
        for i in exp_duration:
            date = search_dates(i)
            if date is not None and len(date) > 0:
                startDate.append(date[0][1].strftime("%m-%Y"))
                if (
                    "present" in i.lower()
                    or "current" in i.lower()
                    or "till date" in i.lower()
                ):
                    endDate.append("present")
                else:
                    endDate.append(date[1][1].strftime("%m-%Y"))
    # print(startDate, endDate)
    work_desc_indices = []
    work_desc = []
    for i in work:
        for ii in range(len(work_segment)):
            if re.search(i, work_segment[ii]):
                #                print(work_segment[ii],i,ii)
                work_desc_indices.append(ii + 1)
                break
    for i in range(len(work_desc_indices)):
        try:
            description = " ".join(
                work_segment[work_desc_indices[i] : work_desc_indices[i + 1] - 1]
            )
        except:
            description = " ".join(
                work_segment[work_desc_indices[i] : len(work_segment)]
            )
        if work == company:
            try:
                for ii in designation:
                    if re.search(ii, description):
                        description = description.replace(ii, "")
                for ii in exp_duration:
                    if re.search(ii.strip(), description):
                        description = description.replace(ii.strip(), "")
            except:
                pass
        else:
            try:
                for ii in company:
                    if re.search(ii, description):
                        description = description.replace(ii, "")
                for ii in exp_duration:
                    if re.search(ii.strip(), description):
                        description = description.replace(ii.strip(), "")
            except:
                pass
        work_desc.append(description)
    if len(work_desc) < len(work):
        for i in range(len(work) - len(work_desc)):
            work_desc.append("")
    #    print(work)
    #    print(work_segment)
    #    print(work_desc_indices)
    #    print(*work_desc, sep ='\n')
    work_locations = extract_location(
        " ".join(work_segment), data_path / "worldcities.csv"
    )
    # print(work_locations)
    for i in range(len(work)):
        if exp_duration != []:
            try:
                work_exp.append(
                    {
                        "company": company[i],
                        "title": designation[i],
                        "startDate": startDate[i],
                        "endDate": endDate[i],
                        "description": work_desc[i],
                    }
                )
            except IndexError:
                if i >= len(startDate):
                    try:
                        work_exp.append(
                            {
                                "company": company[i],
                                "title": designation[i],
                                "startDate": None,
                                "endDate": None,
                                "description": work_desc[i],
                            }
                        )
                    except IndexError:
                        if work == company:
                            work_exp.append(
                                {
                                    "company": company[i],
                                    "title": None,
                                    "startDate": None,
                                    "endDate": None,
                                    "description": work_desc[i],
                                }
                            )
                        else:
                            work_exp.append(
                                {
                                    "company": None,
                                    "title": designation[i],
                                    "startDate": None,
                                    "endDate": None,
                                    "description": work_desc[i],
                                }
                            )
                else:
                    if work == company:
                        work_exp.append(
                            {
                                "company": company[i],
                                "title": None,
                                "startDate": startDate[i],
                                "endDate": endDate[i],
                                "description": work_desc[i],
                            }
                        )
                    else:
                        work_exp.append(
                            {
                                "company": None,
                                "title": designation[i],
                                "startDate": startDate[i],
                                "endDate": endDate[i],
                                "description": work_desc[i],
                            }
                        )
        else:
            try:
                work_exp.append(
                    {
                        "company": company[i],
                        "title": designation[i],
                        "startDate": None,
                        "endDate": None,
                        "description": work_desc[i],
                    }
                )
            except:  # IndexError:
                if work == company:
                    work_exp.append(
                        {
                            "company": company[i],
                            "title": None,
                            "startDate": None,
                            "endDate": None,
                            "description": work_desc[i],
                        }
                    )
                else:
                    work_exp.append(
                        {
                            "company": None,
                            "title": designation[i],
                            "startDate": None,
                            "endDate": None,
                            "description": work_desc[i],
                        }
                    )
    # print(resume_lines)
    return {"total experience": total_exp, "Company Wise Experience": work_exp}


def extract_skills(text_lines, file):
    df = pd.read_csv(file, header=None)
    skill_list = [str(i).upper() for i in list(df[2].unique())]
    skill_list = list(set(skill_list))
    # print(len(skill_list))
    skills = []
    for i in range(len(text_lines)):
        for j in range(len(skill_list)):
            if re.search(
                re.escape(str(skill_list[j]).lower()) + r"\b", text_lines[i].lower()
            ):
                skills.append(skill_list[j])
    return list(set(skills))


def extract_languages(text, path):
    df = pd.read_csv(path, header=None)
    language_list = list(df[1])
    languages = []
    for i in range(len(language_list)):
        for ii in range(len(text)):
            if re.findall(language_list[i].lower(), text[ii].lower()):
                languages.append(language_list[i])
                break
    return languages


def ner_model(text, path):
    model = spacy.load(path)
    doc = model(text)
    return doc


def resume_details(resume_lines, resume_segments):
    data_path = Path("data")
    # print(resume_segments)
    personal = personal_details(resume_lines, resume_segments)
    eduction = education_details(resume_lines, resume_segments)
    work_exp = work_details(resume_lines, resume_segments)
    if resume_segments["skills"] != {}:
        skill_text = []
        for key in resume_segments["skills"]:
            skill_text.extend(resume_segments["skills"][key])
        skills = extract_skills(skill_text, data_path / "skills.csv")
    else:
        skills = []
    hobbies = resume_segments["hobbies"]
    if resume_segments["languages"] != {}:
        lang_text = []
        for key in resume_segments["languages"]:
            lang_text.extend(resume_segments["languages"][key])
        languages = extract_languages(lang_text, data_path / "languages.csv")
    else:
        languages = []
    projects = resume_segments["projects"]
    certificates = resume_segments["certificates"]
    return json.dumps(
        {
            "personal details": personal,
            "educational details": eduction,
            "work experience": work_exp,
            "skills": skills,
            "languages": languages,
            "projects": projects,
            "certificates": certificates,
            "hobbies": hobbies,
        },
        ensure_ascii=False,
    )

