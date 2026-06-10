import streamlit as st
import json
import google.generativeai as genai

# --- CONFIGURE GEMINI ---
API_KEY = "AIzaSyD9lieIajWzJcdFQpgGI4JOit1To7BpaAM"   # replace with your actual Gemini API key
genai.configure(api_key=API_KEY)

# --- INIT SESSION STATE ---
if "profile_completed" not in st.session_state:
    st.session_state.profile_completed = False
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- PHASE 1: QUESTIONNAIRE ---
if not st.session_state.profile_completed:
    st.title("Career Pathfinder - Questionnaire")

    name = st.text_input("Name")
    age = st.number_input("Age", min_value=20, max_value=80, step=1)
    gender = st.radio("Gender", ["Male", "Female", "Other"])

    st.header("Academic Background")

    # Step 1: Highest level of education
    highest_level = st.selectbox(
        "What is the highest level of education you have completed?",
        ["10th", "12th", "Undergraduate (College)", "Postgraduate", "Other"]
    )

    # Initialize profile dict
    academic_profile = {"highest_level": highest_level}

    # Step 2: Collect details based on level
    if highest_level == "10th":
        academic_profile["10th"] = {
            "percentage": st.slider("10th Percentage:", 0, 100, 75)
        }

    elif highest_level == "12th":
        academic_profile["10th"] = {
            "percentage": st.slider("10th Percentage:", 0, 100, 75)
        }
        academic_profile["12th"] = {
            "stream": st.selectbox("Select your 12th stream:", ["Science", "Commerce", "Arts", "Other"]),
            "percentage": st.slider("12th Percentage:", 0, 100, 75)
        }

    elif highest_level in ["Undergraduate (College)", "Postgraduate"]:
        academic_profile["10th"] = {
            "percentage": st.slider("10th Percentage:", 0, 100, 75)
        }
        academic_profile["12th"] = {
            "stream": st.selectbox("Select your 12th stream:", ["Science", "Commerce", "Arts", "Other"]),
            "percentage": st.slider("12th Percentage:", 0, 100, 75)
        }
        academic_profile["college"] = {
            "name": st.text_input("Enter your college name:"),
            "tier": st.selectbox("Select your college tier:", ["Tier 1 (IIT/NIT/IISc)", "Tier 2 (State Universities / Known Pvt Colleges)", "Tier 3 (Local/Other Colleges)"]),
            "degree_type": st.selectbox("Select your degree:", ["B.Tech", "B.Sc", "B.A", "B.Com", "MBA", "MCA", "Other"]),
            "branch": st.text_input("Enter your branch/specialization:"),
            "cgpa":st.slider('Degree cgpa',0,10,7)
        }

    hobbies = st.text_area("What are your hobbies or things you’re good at?")
    internships = st.text_area("Have you done any internships? (if yes, describe)")
    goals = st.text_area("What do you want to become? (Career goal)")
    location = st.text_input("Your Location / City")
    family_condition = st.selectbox("Family Condition", ["Stable", "Middle-class", "Financially Challenged"])
    other_details = st.text_area("Anything else you would like to share")

    if st.button("Submit Profile"):
        profile = {
            "name": name,
            "age": age,
            "gender": gender,
            "academic profile": academic_profile,
            "hobbies": hobbies,
            "internships": internships,
            "goals": goals,
            "location": location,
            "family_condition": family_condition,
            "other details":other_details
        }
        with open("career_profile.json", "w") as f:
            json.dump(profile, f, indent=4)

        st.session_state.profile_completed = True
        st.rerun()

# --- PHASE 2: GUIDANCE CHATBOT ---
else:
    st.title("Career Pathfinder - Guidance Chatbot")
    st.caption("Discuss your career with Pathfinder AI")

    # Load profile from file
    with open("career_profile.json", "r") as f:
        profile = json.load(f)

    # Gemini model
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
    except Exception as e:
        st.error(f"Error loading Gemini model: {e}")
        st.stop()

    # Display previous messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["text"])

    # Chat input
    if user_input := st.chat_input("Ask Pathfinder anything..."):
        # Show user message
        st.session_state.messages.append({"role": "user", "text": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Build context prompt with profile
        context_prompt = f"""
        You are Pathfinder, a tough-love career mentor. 
        Your personality is rational, slightly blunt, and brutally honest, but never insulting without purpose. 
        You mix reality checks with encouragement. 
        If the user asks why they are unemployed, don’t sugarcoat: 
        - Point out gaps in their skills, mindset, or approach. 
        - Compare them against actual job market expectations. 
        - Highlight both external factors (AI, economy, location, family) and internal ones (discipline, skills). 

        BUT, after every harsh truth, show the bright side: 
        - Give them a clear step or resource to improve. 
        - Reframe failure as experience. 
        - Show them opportunities that align with their profile. 

        Your style should feel like a mentor who says: 
        "Here’s why you’re stuck — but here’s how you break out of it." 

        Here is the user profile:
        Name: {profile['name']}
        Age: {profile['age']}
        Gender: {profile['gender']}
        "academic profile": {profile['academic profile']}
        Hobbies/Skills: {profile['hobbies']}
        Internships: {profile['internships']}
        Career Goals: {profile['goals']}
        Location: {profile['location']}
        Family Condition: {profile['family_condition']}

        Your task:
        Suggest **niche and suitable career paths** for the user:
        - Justify *why each career fits them* (use their profile context).
        - Show the requirements for that career.
        - Highlight the gap between their current profile and the job requirements.
        - Keep answers clear, structured, and motivational.
        """

        try:
            chat = model.start_chat(history=[
                {"role": "user", "parts": [{"text": context_prompt}]},
                *[{"role": m["role"], "parts": [{"text": m["text"]}]} for m in st.session_state.messages]
            ])

            response = chat.send_message(user_input)

            # Display model response
            st.session_state.messages.append({"role": "model", "text": response.text})
            with st.chat_message("assistant"):
                st.markdown(response.text)

        except Exception as e:
            st.error(f"Error generating response: {e}")
