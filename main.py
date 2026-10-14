from fastapi import FastAPI
import uvicorn
from mysite.api import auth, application, category, course, enrollment, studygroup, ai, agent
from mysite.admin.setup import setup_admin


coursera_app = FastAPI(title="Coursera app with LLM")
coursera_app.include_router(auth.auth_router)
coursera_app.include_router(category.category_router)
coursera_app.include_router(course.course_router)
coursera_app.include_router(studygroup.studygroup_router)
coursera_app.include_router(application.application_router)
coursera_app.include_router(enrollment.enrollment_router)
coursera_app.include_router(ai.ai_router)
coursera_app.include_router(agent.agent_router)
setup_admin(coursera_app)

if __name__ == "__main__":
    uvicorn.run(coursera_app, host="127.0.0.1", port=8000)