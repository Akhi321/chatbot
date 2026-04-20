import difflib
import re

import pandas as pd

try:
    import google.generativeai as genai
    # Paste your Google Gemini API key inside the quotes below
    GOOGLE_API_KEY = "AIzaSyDgywEZO5Emo5iM_tCeSxJwzrsIcUaD8iM"
    if GOOGLE_API_KEY:
        genai.configure(api_key=GOOGLE_API_KEY)
        GEMINI_AVAILABLE = True
    else:
        GEMINI_AVAILABLE = False
except ImportError:
    GEMINI_AVAILABLE = False

try:
    from sklearn.tree import DecisionTreeClassifier

    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False


SUBJECTS = ["Math", "Science", "English", "History"]
DATASET_URLS = [
    "https://www.dropbox.com/scl/fi/oysmoymawkd3hjh5gzu75/marks.csv?rlkey=czmynpc245n5ts2p1oczkf6gp&st=rrzfcabm&dl=1",
    "https://www.dropbox.com/scl/fi/oysmoymawkd3hjh5gzu75/marks.csv?rlkey=czmynpc245n5ts2p1oczkf6gp&st=yr3rtgbe&dl=1",
]


class NCM_Bot:
    def __init__(self):
        dfs = []

        for index, url in enumerate(DATASET_URLS, start=1):
            try:
                dfs.append(pd.read_csv(url))
            except Exception as e:
                print(f"[ERROR] Could not fetch dataset {index}. {e}")

        if dfs:
            self.df = pd.concat(dfs, ignore_index=True).drop_duplicates(subset=["Name"])
            print(f"[INFO] Successfully combined online datasets! Total students: {len(self.df)}")
        else:
            self.df = None

        self.ml_model = None
        if self.df is not None and ML_AVAILABLE:
            self.train_model()

    def train_model(self):
        """Train a simple decision tree on the student dataset."""
        X = self.df[SUBJECTS]
        y = self.df["Grade"]
        self.ml_model = DecisionTreeClassifier()
        self.ml_model.fit(X, y)

    def _tokenize(self, text):
        return re.findall(r"[a-z0-9+]+", text.lower())

    def _find_student_names(self, query_lower):
        if self.df is None:
            return []

        names_in_df = self.df["Name"].tolist()
        query_words = set(self._tokenize(query_lower))
        
        matches = []

        for name in names_in_df:
            name_lower = name.lower()
            name_parts = name_lower.split()
            if name_lower in query_lower or any(part in query_words for part in name_parts):
                if name not in matches:
                    matches.append(name)

        if matches:
            return matches

        all_parts = []
        for name in names_in_df:
            all_parts.extend(name.lower().split())

        fuzzy_matches = []
        for word in query_words:
            close_matches = difflib.get_close_matches(word, all_parts, n=1, cutoff=0.7)
            if not close_matches:
                continue

            best_match = close_matches[0]
            for name in names_in_df:
                if best_match in name.lower().split():
                    if name not in fuzzy_matches:
                        fuzzy_matches.append(name)

        return fuzzy_matches

    def _format_subject_scores(self, person_data):
        return ", ".join(f"{subject}: {person_data[subject]}" for subject in SUBJECTS)

    def _format_student_details(self, person_data):
        return (
            f"{person_data['Name']}: {self._format_subject_scores(person_data)}, "
            f"Total: {person_data['Total']}, Grade: {person_data['Grade']}"
        )

    def _failed_subjects(self, person_data):
        return [subject for subject in SUBJECTS if person_data[subject] < 50]

    def run(self):
        if self.df is None:
            print("[ERROR] Cannot run the bot because the CSV file could not be downloaded.")
            return

        print("\nHello! I am your NCM AI assistant.")
        if ML_AVAILABLE:
            print("I can also predict grades using a machine learning model trained on the marks dataset.")
            print(" - Ask for a prediction, for example: 'predict marks 85 90 80 75'")
        print(" - Ask questions such as 'What is Alice\\'s grade?' or 'show only C grade'.")
        print(" - Add 'subject only' if you want subject marks without overall totals.")
        print("Type 'exit' to quit.\n")

        while True:
            user_input = input("You: ").strip()
            if user_input.lower() in ["exit", "quit"]:
                break
            if not user_input:
                continue

            response = self.process_query(user_input)
            print(f"Bot: {response}\n")

    def process_query(self, query):
        if GEMINI_AVAILABLE:
            try:
                model = genai.GenerativeModel('gemini-2.5-flash')
                response = model.generate_content(f"You are an expert spelling corrector for a student dataset. Carefully correct the strict grammar and spelling of the following sentence. Return ONLY the perfectly corrected short sentence without any conversational filler or quotes. Do NOT answer the question. Sentence: '{query}'")
                corrected_query = response.text.strip().strip("'\"")
                query_lower = corrected_query.lower()
            except Exception as e:
                query_lower = query.lower()
        else:
            query_lower = query.lower()
            
        df = self.df

        if df is None:
            return "I cannot access the marks dataset right now. Please try again later."

        if "predict" in query_lower and self.ml_model:
            nums = re.findall(r"\d+", query_lower)
            if len(nums) >= 4:
                marks = [int(n) for n in nums[:4]]
                pred_grade = self.ml_model.predict([marks])[0]
                return f"My trained AI model predicts that marks {marks} would result in grade {pred_grade}."
            return (
                "To use the AI predictor, please provide four numbers for Math, Science, "
                "English, and History, for example: 'predict 80 90 85 70'."
            )
        if "predict" in query_lower and not ML_AVAILABLE:
            return (
                "Machine learning support is not installed. Run "
                "`pip install scikit-learn numpy` to enable grade prediction."
            )

        raw_query = query.lower()
        query_words = set(self._tokenize(query_lower))
        subject_only = "subject only" in raw_query or "sub ject only" in raw_query
        only_mark = "only mark" in raw_query or "mark only" in raw_query or "total mark" in raw_query
        wants_details = "all details" in query_lower or "full details" in query_lower or "details" in query_words
        found_names = self._find_student_names(query_lower)

        if found_names:
            responses = []
            for found_name in found_names:
                person_data = df[df["Name"] == found_name].iloc[0]
    
                if "fail" in query_lower:
                    failed_subjects = self._failed_subjects(person_data)
                    if not failed_subjects:
                        responses.append(f"{found_name} has not failed any subjects.")
                    else:
                        if subject_only:
                            failed_list = ", ".join(failed_subjects)
                        else:
                            failed_list = ", ".join(f"{subject} ({person_data[subject]})" for subject in failed_subjects)
                        responses.append(f"{found_name} has failed the following subjects: {failed_list}.")
                    continue
    
                if "grade" in query_lower:
                    responses.append(f"{found_name}'s grade is {person_data['Grade']}.")
                    continue
    
                if only_mark:
                    responses.append(f"{found_name}'s total mark is {person_data['Total']}.")
                    continue
    
                if subject_only:
                    responses.append(f"{found_name}'s subject marks are {self._format_subject_scores(person_data)}.")
                    continue
    
                if len(found_names) > 1:
                    responses.append(
                        f"Details for {found_name}: "
                        f"{self._format_subject_scores(person_data)}, "
                        f"Total: {person_data['Total']}, Grade: {person_data['Grade']}."
                    )
                else:
                    responses.append(
                        f"Here are the mark details for {found_name}: "
                        f"{self._format_subject_scores(person_data)}, "
                        f"Total: {person_data['Total']}, Grade: {person_data['Grade']}."
                    )
            return "\n\n".join(responses)

        if query_words.intersection({"highest", "top", "best", "max", "greatest", "graterst", "high"}):
            nums = re.findall(r"\d+", query_lower)
            n_items = int(nums[0]) if nums else 1
            n_items = min(n_items, len(df))

            for subj in SUBJECTS:
                if subj.lower() in query_lower:
                    if n_items == 1:
                        top_student = df.loc[df[subj].idxmax()]
                        if wants_details:
                            return (
                                f"Here are the full details of the top student in {subj}: "
                                f"{self._format_student_details(top_student)}."
                            )
                        return f"The highest mark in {subj} is {top_student[subj]}, achieved by {top_student['Name']}."
                    else:
                        top_n = df.nlargest(n_items, subj)
                        resp = [f"The highest {n_items} marks in {subj}:"]
                        for _, row in top_n.iterrows():
                            if wants_details:
                                resp.append(f"- {self._format_student_details(row)}")
                            else:
                                resp.append(f"- {row['Name']}: {row[subj]}")
                        return "\n".join(resp)

            if not subject_only:
                if n_items == 1:
                    top_student = df.loc[df["Total"].idxmax()]
                    if wants_details:
                        return (
                            "Here are the full details of the student with the highest total: "
                            f"{self._format_student_details(top_student)}."
                        )
                    return f"The highest overall total is {top_student['Total']}, achieved by {top_student['Name']}."
                else:
                    top_n = df.nlargest(n_items, "Total")
                    resp = [f"The highest {n_items} overall totals:"]
                    for _, row in top_n.iterrows():
                        if wants_details:
                            resp.append(f"- {self._format_student_details(row)}")
                        else:
                            resp.append(f"- {row['Name']}: {row['Total']}")
                    return "\n".join(resp)
                
            top_m = df.loc[df["Math"].idxmax()]
            top_s = df.loc[df["Science"].idxmax()]
            top_e = df.loc[df["English"].idxmax()]
            top_h = df.loc[df["History"].idxmax()]
            return (f"Highest Subject Marks:\n"
                    f"- Math: {top_m['Math']} ({top_m['Name']})\n"
                    f"- Science: {top_s['Science']} ({top_s['Name']})\n"
                    f"- English: {top_e['English']} ({top_e['Name']})\n"
                    f"- History: {top_h['History']} ({top_h['Name']})")

        if query_words.intersection({"lowest", "low", "worst", "min", "minimum", "poor"}):
            nums = re.findall(r"\d+", query_lower)
            n_items = int(nums[0]) if nums else 1
            n_items = min(n_items, len(df))

            for subj in SUBJECTS:
                if subj.lower() in query_lower:
                    if n_items == 1:
                        low = df.loc[df[subj].idxmin()]
                        if wants_details:
                            return (
                                f"Here are the full details of the student with the lowest mark in {subj}: "
                                f"{self._format_student_details(low)}."
                            )
                        return f"The lowest mark in {subj} is {low[subj]}, scored by {low['Name']}."
                    else:
                        bottom_n = df.nsmallest(n_items, subj)
                        resp = [f"The lowest {n_items} marks in {subj}:"]
                        for _, row in bottom_n.iterrows():
                            if wants_details:
                                resp.append(f"- {self._format_student_details(row)}")
                            else:
                                resp.append(f"- {row['Name']}: {row[subj]}")
                        return "\n".join(resp)
            
            if n_items == 1:
                low = df.loc[df["Total"].idxmin()]
                if wants_details:
                    return (
                        "Here are the full details of the student with the lowest total: "
                        f"{self._format_student_details(low)}."
                    )
                return f"The lowest overall total is {low['Total']}, scored by {low['Name']}."
            else:
                bottom_n = df.nsmallest(n_items, "Total")
                resp = [f"The lowest {n_items} overall totals:"]
                for _, row in bottom_n.iterrows():
                    if wants_details:
                        resp.append(f"- {self._format_student_details(row)}")
                    else:
                        resp.append(f"- {row['Name']}: {row['Total']}")
                return "\n".join(resp)

        if "fail" in query_lower:
            failed_students = []
            for _, row in df.iterrows():
                failed_subjects = [subject for subject in SUBJECTS if row[subject] < 50]
                if failed_subjects:
                    if subject_only:
                        subject_list = ", ".join(failed_subjects)
                    else:
                        subject_list = ", ".join(f"{subject} ({row[subject]})" for subject in failed_subjects)
                    failed_students.append(f"{row['Name']}: {subject_list}")
            if not failed_students:
                return "No students have failed any subjects."
            return "Here are the students who failed subjects:\n" + "\n".join(
                f"- {student}" for student in failed_students
            )

        if "pass" in query_lower:
            passed_students = []
            for _, row in df.iterrows():
                if all(row[subject] >= 50 for subject in SUBJECTS):
                    passed_students.append(row["Name"])
                    
            if not passed_students:
                return "No students passed all subjects."
            
            if len(passed_students) > 20:
                return f"{len(passed_students)} students successfully passed all subjects."
                
            return "Students who passed all subjects:\n" + "\n".join(f"- {name}" for name in passed_students)

        if "grade" in query_lower:
            target_grade = None
            words = self._tokenize(query_lower)
            for g in ["a+", "a", "b", "c"]:
                if g in words or f"{g} grade" in query_lower or f"grade {g}" in query_lower:
                    target_grade = g.upper()
                    break

            if target_grade:
                grade_students = df[df["Grade"].str.upper() == target_grade]
                if grade_students.empty:
                    return f"No students found with Grade {target_grade}."
                resp = [f"Here are the students with Grade {target_grade}:"]
                for _, row in grade_students.iterrows():
                    if subject_only:
                        resp.append(f"- {row['Name']}: {self._format_subject_scores(row)}")
                    else:
                        resp.append(
                            f"- {row['Name']}: {self._format_subject_scores(row)}, Total: {row['Total']}"
                        )
                return "\n".join(resp)

        if "all" in query_lower.split():
            resp = ["Here are all the students:"]
            for _, row in df.iterrows():
                resp.append(f"- {row['Name']}: {row['Total']} marks (Grade {row['Grade']})")
            return "\n".join(resp)

        clean_q = query_lower.strip(" ?!.,;\n")
        is_greeting = clean_q in ["who", "who are you", "who are u", "who r u", "what are you"]
        is_greeting = is_greeting or (clean_q.startswith(('hi', 'hey', 'hello')) and len(clean_q.split()) <= 2)
        
        if is_greeting:
            return (
                "Hello! I am the NCM Chatbot for Nehru College of Management. "
                "I can help you check marks, grades, and simple predictions."
            )

        words = query_lower.strip(" ?!.").split()
        if "score" in query_lower or "grade" in query_lower or "mark" in query_lower or len(words) <= 2:
            return "I could not find that student. Please check the name and try again."

        return (
            "I could not understand that request. Try asking for a student's grade, "
            "the highest mark in a subject, or a prediction using four subject marks."
        )

def main():
    bot = NCM_Bot()
    bot.run()

if __name__ == "__main__":
    main()
