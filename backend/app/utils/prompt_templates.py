"""
Structured prompt templates for different types of meeting summaries and analysis.
"""

from typing import Dict, List, Optional
from enum import Enum


class PromptTemplate(Enum):
    """Enum for different prompt templates."""
    EXECUTIVE_SUMMARY = "executive_summary"
    DETAILED_SUMMARY = "detailed_summary"
    KEY_DECISIONS = "key_decisions"
    ACTION_ITEMS = "action_items"
    RISKS = "risks"
    OPEN_QUESTIONS = "open_questions"
    KEYWORDS = "keywords"


class PromptTemplateManager:
    """Manager for prompt templates with context injection."""
    
    @staticmethod
    def get_executive_summary_prompt(transcript: str, context: Optional[str] = None) -> str:
        """Generate executive summary prompt."""
        base_prompt = """You are an expert meeting analyst. Create a concise executive summary of the following meeting transcript.

Focus on:
- Main topics discussed
- Key outcomes and decisions
- Important action items
- Overall meeting effectiveness

Context: {context}

Transcript:
{transcript}

Provide a structured executive summary in 3-4 paragraphs. Be concise but comprehensive."""
        
        return base_prompt.format(
            context=context or "No additional context provided.",
            transcript=transcript
        )
    
    @staticmethod
    def get_detailed_summary_prompt(transcript: str, context: Optional[str] = None) -> str:
        """Generate detailed summary prompt."""
        base_prompt = """You are an expert meeting analyst. Create a comprehensive detailed summary of the following meeting transcript.

Include:
- Detailed discussion of each topic
- All decisions made with reasoning
- Complete action items with context
- Key insights and observations
- Timeline of discussion flow

Context: {context}

Transcript:
{transcript}

Provide a thorough, well-structured summary that captures all important details discussed in the meeting."""
        
        return base_prompt.format(
            context=context or "No additional context provided.",
            transcript=transcript
        )
    
    @staticmethod
    def get_key_decisions_prompt(transcript: str, context: Optional[str] = None) -> str:
        """Generate key decisions extraction prompt."""
        base_prompt = """You are an expert meeting analyst. Extract all key decisions made during this meeting from the transcript.

For each decision, provide:
1. Clear description of the decision
2. Who made the decision (if mentioned)
3. Rationale or reasoning (if provided)
4. Impact or implications (if discussed)

Context: {context}

Transcript:
{transcript}

Return the decisions as a JSON array with objects containing: "description", "decision_maker", "rationale", "impact", and "timestamp" (if mentioned). If no clear decisions were made, return an empty array."""
        
        return base_prompt.format(
            context=context or "No additional context provided.",
            transcript=transcript
        )
    
    @staticmethod
    def get_action_items_prompt(transcript: str, context: Optional[str] = None) -> str:
        """Generate action items extraction prompt."""
        base_prompt = """You are an expert meeting analyst. Extract all action items and tasks assigned during this meeting from the transcript.

For each action item, identify:
1. Clear description of the task/action
2. Person responsible (owner/assignee)
3. Deadline or timeframe (if mentioned)
4. Priority level (high/medium/low based on discussion tone)
5. Dependencies (if any)

Context: {context}

Transcript:
{transcript}

Return the action items as a JSON array with objects containing: "description", "owner", "deadline", "priority", "dependencies", and "status" (default to "open"). If no action items were identified, return an empty array."""
        
        return base_prompt.format(
            context=context or "No additional context provided.",
            transcript=transcript
        )
    
    @staticmethod
    def get_risks_prompt(transcript: str, context: Optional[str] = None) -> str:
        """Generate risks identification prompt."""
        base_prompt = """You are an expert meeting analyst and risk assessment specialist. Identify potential risks, concerns, or issues mentioned or implied in this meeting transcript.

For each risk, analyze:
1. Clear description of the risk or concern
2. Impact level (high/medium/low)
3. Probability of occurrence (high/medium/low)
4. Potential mitigation strategies (if discussed)
5. Risk category (technical, business, operational, etc.)

Context: {context}

Transcript:
{transcript}

Return the risks as a JSON array with objects containing: "description", "impact", "probability", "mitigation", "category". If no risks were identified, return an empty array."""
        
        return base_prompt.format(
            context=context or "No additional context provided.",
            transcript=transcript
        )
    
    @staticmethod
    def get_open_questions_prompt(transcript: str, context: Optional[str] = None) -> str:
        """Generate open questions extraction prompt."""
        base_prompt = """You are an expert meeting analyst. Identify all open questions, unresolved issues, or topics that need follow-up from this meeting transcript.

For each open question, provide:
1. Clear description of the question or unresolved issue
2. Context or background (why this is important)
3. Who should address it (if mentioned or suggested)
4. Urgency level (high/medium/low)

Context: {context}

Transcript:
{transcript}

Return the open questions as a JSON array with objects containing: "question", "context", "assigned_to", "urgency". If no open questions were identified, return an empty array."""
        
        return base_prompt.format(
            context=context or "No additional context provided.",
            transcript=transcript
        )
    
    @staticmethod
    def get_keywords_prompt(transcript: str, context: Optional[str] = None) -> str:
        """Generate keywords extraction prompt."""
        base_prompt = """You are an expert meeting analyst. Extract key topics, concepts, and important terms mentioned in this meeting transcript.

Focus on:
- Main topics and themes
- Technical terms and concepts
- Project names and initiatives
- Important business terms
- People, companies, or organizations mentioned
- Tools, technologies, or systems discussed

Context: {context}

Transcript:
{transcript}

Return a JSON array of relevant keywords and key phrases (10-20 items). Focus on the most important and frequently mentioned terms that would help categorize and search this meeting."""
        
        return base_prompt.format(
            context=context or "No additional context provided.",
            transcript=transcript
        )
    
    @staticmethod
    def get_comprehensive_analysis_prompt(transcript: str, context: Optional[str] = None) -> str:
        """Generate comprehensive analysis prompt that covers all aspects."""
        base_prompt = """You are an expert meeting analyst. Provide a comprehensive analysis of this meeting transcript covering all important aspects.

Please analyze and provide:

1. EXECUTIVE SUMMARY (2-3 paragraphs)
2. DETAILED SUMMARY (comprehensive breakdown)
3. KEY DECISIONS (with decision makers and rationale)
4. ACTION ITEMS (with owners, deadlines, and priorities)
5. RISKS AND CONCERNS (with impact and mitigation strategies)
6. OPEN QUESTIONS (unresolved issues needing follow-up)
7. KEYWORDS (important terms and topics)

Context: {context}

Transcript:
{transcript}

Return a JSON object with the following structure:
{{
  "executive_summary": "...",
  "detailed_summary": "...",
  "key_decisions": [...],
  "action_items": [...],
  "risks": [...],
  "open_questions": [...],
  "keywords": [...]
}}

Each array should contain objects with appropriate fields as defined in the individual prompts above."""
        
        return base_prompt.format(
            context=context or "No additional context provided.",
            transcript=transcript
        )
    
    @classmethod
    def get_prompt(
        cls, 
        template_type: PromptTemplate, 
        transcript: str, 
        context: Optional[str] = None
    ) -> str:
        """Get prompt by template type."""
        template_methods = {
            PromptTemplate.EXECUTIVE_SUMMARY: cls.get_executive_summary_prompt,
            PromptTemplate.DETAILED_SUMMARY: cls.get_detailed_summary_prompt,
            PromptTemplate.KEY_DECISIONS: cls.get_key_decisions_prompt,
            PromptTemplate.ACTION_ITEMS: cls.get_action_items_prompt,
            PromptTemplate.RISKS: cls.get_risks_prompt,
            PromptTemplate.OPEN_QUESTIONS: cls.get_open_questions_prompt,
            PromptTemplate.KEYWORDS: cls.get_keywords_prompt,
        }
        
        method = template_methods.get(template_type)
        if not method:
            raise ValueError(f"Unknown template type: {template_type}")
        
        return method(transcript, context)
    
    @classmethod
    def get_all_templates(cls) -> List[PromptTemplate]:
        """Get list of all available templates."""
        return list(PromptTemplate)


# Example usage and testing
if __name__ == "__main__":
    # Test the prompt templates
    sample_transcript = """
    John: Good morning everyone, thanks for joining the weekly team meeting.
    Sarah: Morning John. Should we start with the project updates?
    John: Yes, let's do that. Sarah, can you give us an update on the marketing campaign?
    Sarah: Sure. We've completed the design phase and we're ready to move to implementation. 
    However, we're facing some budget constraints that we need to address.
    Mike: What's the budget shortfall?
    Sarah: We're about $5000 short for the digital advertising component.
    John: That's concerning. Mike, can you work with Sarah to find alternative solutions by Friday?
    Mike: Absolutely. I'll review our options and get back to you both by end of week.
    John: Great. Any other risks we should be aware of?
    Sarah: The timeline is tight. If we don't resolve the budget issue quickly, 
    we might need to push the launch date back by two weeks.
    """
    
    template_manager = PromptTemplateManager()
    
    # Test executive summary prompt
    exec_prompt = template_manager.get_executive_summary_prompt(
        sample_transcript, 
        "Weekly marketing team meeting"
    )
    print("Executive Summary Prompt:")
    print(exec_prompt)
    print("\n" + "="*80 + "\n")
    
    # Test action items prompt
    action_prompt = template_manager.get_action_items_prompt(
        sample_transcript, 
        "Weekly marketing team meeting"
    )
    print("Action Items Prompt:")
    print(action_prompt)