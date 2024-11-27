# Academic Advisor Chatbot System

This project addresses the pressing issue of unfavorable advisor-to-student ratios in academic institutions by creating a **chatbot-based system** to support students. The system's goal is to alleviate the workload of academic advisors while providing timely and efficient assistance to students in areas like degree navigation, course planning, and addressing queries.Made for fulfilling CSE 512 project requirements.

---

## Key Features

1. **Degree Navigation**:  
   Helps students design and navigate their degree plans from the beginning, ensuring structured progress.
   
2. **ALEKS Integration**:  
   Utilizes **ALEKS scores** to recommend suitable courses, aligning with students' capabilities and goals.
   
3. **Smart Search**:  
   Leverages **ElasticSearch** to enable robust and efficient course discovery across multiple campuses.

4. **Course Completion List**:  
   Generates customized plans for students, detailing completed and pending courses.

5. **Self-Service Assistance**:  
   Answers common student queries, reducing reliance on academic advisors for routine questions.

6. **User-Friendly Interface**:  
   Simplifies course selection and planning with an intuitive interface.

---

## Technologies Used

### **Frontend**  
- Built using **Next.js**, offering a modern and performant UI.  
  **Commands to Set Up and Run**:  
  ```bash
  cd my-app
  yarn add . # or npm install
  npm run dev
  ```

### **Backend**  
- Developed using **Flask** and **ElasticSearch** for a powerful backend service.  
  **Dependencies**:  
  ```bash
  pip install elasticsearch openai flask flask-cors
  ```  
  **Command to Run**:  
  ```bash
  python3 app.py
  ```
### Requirements: 
1.Open AI API key: 
2. Elastic Search API Credentials:
