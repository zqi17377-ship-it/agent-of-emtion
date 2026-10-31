from .schemas import SessionState, EligibilityContext, InquiryState


def new_session():
    return SessionState()


def clear_session(session):
    session.messages.clear()
    session.previous_decision = None
    session.eligibility = EligibilityContext()
    session.inquiry_state = InquiryState()
