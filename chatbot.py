import difflib
import os
import re

import pandas as pd


DATASET_CANDIDATES = [
    "student_data.xlsx",
    "cleaned_data.csv",
    "data.csv",
]

COLUMN_ALIASES = {
    "name": "Name",
    "name*": "Name",
    "dob(yyyy-mm-dd)*": "dob",
    "email": "email",
    "email*(gmail)": "email",
    "course": "course",
    "course*": "course",
    "department": "department",
    "department*": "department",
    "rollnumber": "rollNumber",
    "rollnumber*": "rollNumber",
    "batch": "batch",
    "batch*": "batch",
    "gender": "gender",
    "gender*": "gender",
    "collegename": "collegeName",
    "collegename*": "collegeName",
    "ugcgpa/percentage": "UG CGPA",
    "pgcgpa/percentage": "PG CGPA",
    "10th percentage": "tenthPercentage",
    "12th percentage": "twelfthPercentage",
    "contact number": "contact",
    "contact": "contact",
    "standing arrears": "Standing Arrears",
    "history of arrears": "History of Arrears",
}

DISPLAY_FIELDS = [
    ("Roll Number", "rollNumber"),
    ("Department", "department"),
    ("Course", "course"),
    ("Batch", "batch"),
    ("Gender", "gender"),
    ("Email", "email"),
    ("Contact", "contact"),
    ("UG CGPA", "UG CGPA"),
    ("PG CGPA", "PG CGPA"),
    ("10th Percentage", "tenthPercentage"),
    ("12th Percentage", "twelfthPercentage"),
    ("Standing Arrears", "Standing Arrears"),
    ("History of Arrears", "History of Arrears"),
]

NUMERIC_METRICS = [
    "UG CGPA",
    "PG CGPA",
    "tenthPercentage",
    "twelfthPercentage",
    "Standing Arrears",
    "History of Arrears",
]


class NCM_Bot:
    def __init__(self):
        print("[INFO] Initializing NCM Student Bot...")
        self.df = self._load_dataset()

        if self.df is not None:
            print(f"[INFO] Loaded {len(self.df)} student records.")

    def _load_dataset(self):
        for dataset_path in DATASET_CANDIDATES:
            if not os.path.exists(dataset_path):
                continue

            try:
                if dataset_path.lower().endswith(".xlsx"):
                    df = pd.read_excel(dataset_path, engine="openpyxl")
                else:
                    df = pd.read_csv(dataset_path)
                return self._prepare_dataframe(df)
            except Exception as e:
                print(f"[ERROR] Could not load {dataset_path}. {e}")

        print("[ERROR] No supported dataset file could be loaded.")
        return None

    def _prepare_dataframe(self, df):
        df = df.copy()
        df.columns = [str(column).strip() for column in df.columns]

        rename_map = {}
        for column in df.columns:
            alias = COLUMN_ALIASES.get(column.strip().lower())
            if alias:
                rename_map[column] = alias
        df = df.rename(columns=rename_map)

        unnamed_columns = [column for column in df.columns if column.lower().startswith("unnamed")]
        if unnamed_columns:
            df = df.drop(columns=unnamed_columns)

        for column in df.columns:
            if df[column].dtype == "object":
                df[column] = df[column].fillna("").astype(str).str.strip()

        if "Name" in df.columns:
            df = df[df["Name"] != ""]

        for column in NUMERIC_METRICS:
            if column in df.columns:
                df[column] = pd.to_numeric(df[column], errors="coerce")

        return df.reset_index(drop=True)

    def _tokenize(self, text):
        return re.findall(r"[a-z0-9+]+", text.lower())

    def _format_value(self, value):
        if pd.isna(value) or value == "":
            return "N/A"
        if isinstance(value, float):
            if value.is_integer():
                return str(int(value))
            return f"{value:.2f}"
        return str(value)

    def _format_student_details(self, row):
        lines = [f"Name: {row.get('Name', 'N/A')}"]
        for label, column in DISPLAY_FIELDS:
            if column not in self.df.columns:
                continue
            value = row.get(column, "")
            if pd.isna(value) or value == "":
                continue
            lines.append(f"{label}: {self._format_value(value)}")
        return "\n".join(lines)

    def _extract_limit(self, query_lower):
        numbers = re.findall(r"\d+", query_lower)
        if not numbers:
            return 1
        return max(1, int(numbers[0]))

    def _find_student_row(self, query_lower):
        query_words = set(self._tokenize(query_lower))
        query_digits = re.sub(r"\D", "", query_lower)
        matches = []

        for index, row in self.df.iterrows():
            score = 0
            name = str(row.get("Name", "")).strip()
            roll_number = str(row.get("rollNumber", "")).strip().lower()
            email = str(row.get("email", "")).strip().lower()
            contact = re.sub(r"\D", "", str(row.get("contact", "")))

            if not name:
                continue

            name_lower = name.lower()
            name_words = set(self._tokenize(name_lower))

            if query_lower == name_lower:
                score = 100
            elif roll_number and query_lower == roll_number:
                score = 96
            elif email and query_lower == email:
                score = 94
            elif query_lower in name_lower:
                score = 90
            elif roll_number and query_lower in roll_number:
                score = 86
            elif query_digits and contact and query_digits in contact:
                score = 84
            else:
                overlap = len(query_words.intersection(name_words))
                if overlap:
                    score = 60 + (overlap * 8)
                else:
                    for word in query_words:
                        if difflib.get_close_matches(word, list(name_words), n=1, cutoff=0.85):
                            score = max(score, 56)

            if score:
                matches.append((score, index))

        if not matches:
            return None

        matches.sort(reverse=True)
        return self.df.loc[matches[0][1]]

    def _match_category_value(self, query_lower, column):
        if column not in self.df.columns:
            return None

        query_words = set(self._tokenize(query_lower))
        best_value = None
        best_score = 0

        for raw_value in self.df[column].dropna().astype(str).str.strip().unique():
            if not raw_value:
                continue

            value_lower = raw_value.lower()
            value_words = set(self._tokenize(value_lower))

            if value_lower in query_lower:
                return raw_value

            score = len(query_words.intersection(value_words))
            if score > best_score:
                best_score = score
                best_value = raw_value

        if best_score > 0:
            return best_value

        return None

    def _detect_metric(self, query_lower):
        query_words = set(self._tokenize(query_lower))

        if "history" in query_words and "arrears" in query_words and "History of Arrears" in self.df.columns:
            return "History of Arrears"
        if "arrears" in query_words and "Standing Arrears" in self.df.columns:
            return "Standing Arrears"
        if "pg" in query_words and "cgpa" in query_words and "PG CGPA" in self.df.columns:
            return "PG CGPA"
        if "cgpa" in query_words and "UG CGPA" in self.df.columns:
            return "UG CGPA"
        if ("10th" in query_lower or "tenth" in query_words) and "tenthPercentage" in self.df.columns:
            return "tenthPercentage"
        if ("12th" in query_lower or "twelfth" in query_words) and "twelfthPercentage" in self.df.columns:
            return "twelfthPercentage"

        for metric in [
            "UG CGPA",
            "PG CGPA",
            "tenthPercentage",
            "twelfthPercentage",
            "Standing Arrears",
            "History of Arrears",
        ]:
            if metric in self.df.columns:
                return metric

        return None

    def _metric_label(self, metric):
        labels = {
            "UG CGPA": "UG CGPA",
            "PG CGPA": "PG CGPA",
            "tenthPercentage": "10th Percentage",
            "twelfthPercentage": "12th Percentage",
            "Standing Arrears": "Standing Arrears",
            "History of Arrears": "History of Arrears",
        }
        return labels.get(metric, metric)

    def _build_chart(self, title, rows, metric):
        if metric not in rows.columns or "Name" not in rows.columns:
            return []

        chart_rows = rows[["Name", metric]].dropna()
        if chart_rows.empty:
            return []

        return [
            {
                "title": title,
                "labels": chart_rows["Name"].astype(str).tolist(),
                "data": chart_rows[metric].astype(float).round(2).tolist(),
            }
        ]

    def _help_response(self):
        return (
            "Try asking things like:\n"
            "- show details for a student name or roll number\n"
            "- top 5 ug cgpa\n"
            "- lowest 3 standing arrears\n"
            "- students in a department\n"
            "- summary\n"
            "- list students with arrears"
        )

    def _summary_response(self):
        lines = [f"Total students: {len(self.df)}"]

        if "department" in self.df.columns:
            lines.append(f"Departments: {self.df['department'].nunique()}")
        if "course" in self.df.columns:
            lines.append(f"Courses: {self.df['course'].nunique()}")
        if "UG CGPA" in self.df.columns:
            lines.append(f"Average UG CGPA: {self.df['UG CGPA'].dropna().mean():.2f}")
        if "Standing Arrears" in self.df.columns:
            arrears_count = int((self.df["Standing Arrears"].fillna(0) > 0).sum())
            lines.append(f"Students with standing arrears: {arrears_count}")

        return "\n".join(lines)

    def _department_response(self, query_lower):
        for column, label in [("department", "department"), ("course", "course"), ("batch", "batch")]:
            value = self._match_category_value(query_lower, column)
            if not value:
                continue

            filtered = self.df[self.df[column].astype(str).str.lower() == str(value).lower()]
            if filtered.empty:
                continue

            lines = [f"Students in {label} '{value}' ({len(filtered)} found):"]
            for _, row in filtered.head(10).iterrows():
                lines.append(f"- {row.get('Name', 'N/A')}")
            if len(filtered) > 10:
                lines.append(f"...and {len(filtered) - 10} more.")
            return "\n".join(lines)

        return None

    def _arrears_response(self, query_lower):
        if "History of Arrears" in self.df.columns and "history" in query_lower:
            metric = "History of Arrears"
        else:
            metric = "Standing Arrears"

        if metric not in self.df.columns:
            return None

        filtered = self.df[self.df[metric].fillna(0) > 0].sort_values(metric, ascending=False)
        if filtered.empty:
            return {"response": f"No students have {self._metric_label(metric).lower()}."}

        limit = min(self._extract_limit(query_lower), len(filtered), 10)
        result = filtered.head(limit)
        lines = [f"Students with {self._metric_label(metric).lower()}:"]
        for _, row in result.iterrows():
            lines.append(f"- {row.get('Name', 'N/A')}: {self._format_value(row.get(metric))}")

        return {
            "response": "\n".join(lines),
            "charts": self._build_chart(self._metric_label(metric), result, metric),
        }

    def _ranking_response(self, query_lower):
        query_words = set(self._tokenize(query_lower))
        is_top = bool(query_words.intersection({"top", "highest", "best", "max", "maximum"}))
        is_bottom = bool(query_words.intersection({"low", "lowest", "bottom", "worst", "min", "minimum"}))

        if not is_top and not is_bottom:
            return None

        metric = self._detect_metric(query_lower)
        if not metric or metric not in self.df.columns:
            return {
                "response": (
                    "I could not find a numeric metric to rank. "
                    "Try UG CGPA, 10th percentage, 12th percentage, or arrears."
                )
            }

        limit = min(self._extract_limit(query_lower), len(self.df), 10)
        wants_details = "all details" in query_lower or "full details" in query_lower or "details" in query_words
        metric_label = self._metric_label(metric)
        ranking = self.df.dropna(subset=[metric])

        if ranking.empty:
            return {"response": f"I do not have enough data to rank students by {metric_label}."}

        ranking = ranking.nlargest(limit, metric) if is_top else ranking.nsmallest(limit, metric)

        title = (
            f"Top {limit} students by {metric_label}:"
            if is_top
            else f"Lowest {limit} students by {metric_label}:"
        )

        lines = [title]
        for _, row in ranking.iterrows():
            if wants_details:
                lines.append(f"- {self._format_student_details(row)}")
            else:
                lines.append(f"- {row.get('Name', 'N/A')}: {self._format_value(row.get(metric))}")

        return {
            "response": "\n".join(lines),
            "charts": self._build_chart(metric_label, ranking, metric),
        }

    def run(self):
        if self.df is None:
            print("[ERROR] Cannot run the bot because the dataset could not be loaded.")
            return

        print("\nHello! I am your NCM student assistant.")
        print(" - Ask about a student by name or roll number.")
        print(" - Try queries like 'top 5 UG CGPA', 'summary', or 'students with arrears'.")
        print("Type 'exit' to quit.\n")

        while True:
            user_input = input("You: ").strip()
            if user_input.lower() in ["exit", "quit"]:
                break
            if not user_input:
                continue

            response = self.process_query(user_input)
            if isinstance(response, dict):
                print(f"Bot: {response.get('response', '')}\n")
            else:
                print(f"Bot: {response}\n")

    def process_query(self, query):
        if self.df is None:
            return "I cannot access the student dataset right now. Please try again later."

        query_lower = query.lower().strip()
        clean_q = query_lower.strip(" ?!.,;\n")
        clean_words = set(self._tokenize(clean_q))

        is_greeting = clean_q in ["who", "who are you", "who are u", "who r u", "what are you"]
        is_greeting = is_greeting or (clean_q.startswith(("hi", "hey", "hello")) and len(clean_q.split()) <= 2)

        if is_greeting:
            return (
                "Hello! I am the NCM Chatbot for Nehru College of Management. "
                "I can help with student details, rankings, summaries, and arrears."
            )

        if clean_words.intersection({"help", "commands", "examples"}):
            return self._help_response()

        if "summary" in clean_words or "overview" in clean_words or "total students" in query_lower or "how many students" in query_lower:
            return self._summary_response()

        ranking_response = self._ranking_response(query_lower)
        if ranking_response:
            return ranking_response

        if "arrears" in clean_words and clean_words.intersection({"who", "show", "list", "students"}):
            arrears_response = self._arrears_response(query_lower)
            if arrears_response:
                return arrears_response

        if clean_words.intersection({"department", "course", "batch", "students"}) or "students in" in query_lower:
            department_response = self._department_response(query_lower)
            if department_response:
                return department_response

        student_row = self._find_student_row(query_lower)
        if student_row is not None:
            return self._format_student_details(student_row)

        return (
            "I could not find a matching student or command. "
            "Try 'help', a student name, 'summary', or 'top 5 ug cgpa'."
        )


def main():
    bot = NCM_Bot()
    bot.run()


if __name__ == "__main__":
    main()
