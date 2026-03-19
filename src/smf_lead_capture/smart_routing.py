"""Smart lead routing with business rules engine."""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, time
from typing import Any, Callable, Dict, List, Optional, Set

from .ml_scoring import MLLeadScorer, PredictiveRouter

logger = logging.getLogger(__name__)


@dataclass
class RoutingRule:
    """Defines a routing rule with conditions and actions."""
    id: str
    name: str
    priority: int  # Higher = evaluated first
    conditions: List[Dict[str, Any]]
    actions: List[Dict[str, Any]]
    enabled: bool = True


class BusinessRulesEngine:
    """Rule-based routing engine with condition evaluation."""
    
    def __init__(self):
        """Initialize rules engine."""
        self.rules: List[RoutingRule] = []
        self.operators = self._build_operators()
    
    def _build_operators(self) -> Dict[str, Callable]:
        """Build condition operators."""
        return {
            'eq': lambda a, b: a == b,
            'ne': lambda a, b: a != b,
            'gt': lambda a, b: a > b,
            'gte': lambda a, b: a >= b,
            'lt': lambda a, b: a < b,
            'lte': lambda a, b: a <= b,
            'contains': lambda a, b: b.lower() in str(a).lower() if a else False,
            'startswith': lambda a, b: str(a).lower().startswith(b.lower()),
            'endswith': lambda a, b: str(a).lower().endswith(b.lower()),
            'in': lambda a, b: a in b if isinstance(b, (list, tuple, set)) else False,
            'not_in': lambda a, b: a not in b if isinstance(b, (list, tuple, set)) else True,
            'exists': lambda a, b: bool(a) if b else not bool(a),
            'regex': lambda a, b: bool(__import__('re').match(b, str(a))) if a else False,
        }
    
    def add_rule(self, rule: RoutingRule):
        """Add a routing rule."""
        self.rules.append(rule)
        self.rules.sort(key=lambda r: r.priority, reverse=True)
        logger.info(f"Added routing rule: {rule.name} (priority {rule.priority})")
    
    def evaluate_conditions(self, conditions: List[Dict[str, Any]], 
                           context: Dict[str, Any]) -> bool:
        """Evaluate conditions against context.
        
        All conditions must match (AND logic).
        """
        for condition in conditions:
            field = condition.get('field')
            operator = condition.get('operator', 'eq')
            value = condition.get('value')
            
            # Get field value from context
            field_value = self._get_nested_value(context, field)
            
            # Evaluate condition
            op_func = self.operators.get(operator)
            if not op_func:
                logger.warning(f"Unknown operator: {operator}")
                return False
            
            if not op_func(field_value, value):
                return False
        
        return True
    
    def _get_nested_value(self, context: Dict[str, Any], field: str) -> Any:
        """Get nested value from context using dot notation."""
        keys = field.split('.')
        value = context
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        
        return value
    
    def evaluate_rules(self, lead_data: Dict[str, Any],
                      conversation_data: Optional[Dict] = None) -> List[RoutingRule]:
        """Evaluate all rules and return matching ones."""
        context = {
            'lead': lead_data,
            'conversation': conversation_data or {},
            'timestamp': datetime.now().isoformat(),
            'hour': datetime.now().hour,
            'day_of_week': datetime.now().weekday(),
            'is_weekend': datetime.now().weekday() >= 5,
            'is_business_hours': 9 <= datetime.now().hour < 17
        }
        
        matching_rules = []
        
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            try:
                if self.evaluate_conditions(rule.conditions, context):
                    matching_rules.append(rule)
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.id}: {e}")
        
        return matching_rules


class SmartLeadRouter:
    """Intelligent lead routing combining rules, ML, and predictive routing."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize smart router."""
        self.config = config
        self.rules_engine = BusinessRulesEngine()
        self.ml_scorer = MLLeadScorer()
        self.predictive_router = PredictiveRouter(config)
        
        # Load default rules
        self._load_default_rules()
    
    def _load_default_rules(self):
        """Load default routing rules."""
        default_rules = [
            # VIP rule
            RoutingRule(
                id="vip_customers",
                name="VIP Customer Routing",
                priority=100,
                conditions=[
                    {'field': 'lead.email', 'operator': 'endswith', 'value': '@enterprise.com'},
                    {'field': 'lead.score', 'operator': 'gte', 'value': 80}
                ],
                actions=[
                    {'type': 'notify_immediately', 'channel': 'sms', 'priority': 'urgent'},
                    {'type': 'assign_to', 'agent_id': 'vip_team'},
                    {'type': 'create_task', 'title': 'VIP Lead Follow-up', 'due_hours': 1}
                ]
            ),
            
            # Hot lead rule
            RoutingRule(
                id="hot_leads",
                name="Hot Lead Immediate Response",
                priority=90,
                conditions=[
                    {'field': 'lead.score_category', 'operator': 'eq', 'value': 'hot'},
                    {'field': 'lead.qualification_data.budget', 'operator': 'in', 
                     'value': ['50k_plus', '25k_to_50k']}
                ],
                actions=[
                    {'type': 'notify_immediately', 'channel': 'sms'},
                    {'type': 'add_to_sequence', 'sequence': 'hot_lead_nurture'},
                    {'type': 'create_crm_entry', 'pipeline': 'hot_leads', 'stage': 'new'}
                ]
            ),
            
            # Business hours rule
            RoutingRule(
                id="after_hours",
                name="After Hours Auto-Response",
                priority=80,
                conditions=[
                    {'field': 'is_business_hours', 'operator': 'eq', 'value': False}
                ],
                actions=[
                    {'type': 'send_message', 'template': 'after_hours_response'},
                    {'type': 'schedule_followup', 'hours': 9, 'next_business_day': True},
                    {'type': 'notify_team', 'message': 'After-hours lead captured'}
                ]
            ),
            
            # Geographic rule
            RoutingRule(
                id="local_leads",
                name="Local Lead Priority",
                priority=70,
                conditions=[
                    {'field': 'lead.metadata.timezone', 'operator': 'in', 
                     'value': ['America/New_York', 'America/Chicago']}
                ],
                actions=[
                    {'type': 'tag', 'tag': 'local_lead'},
                    {'type': 'assign_to', 'agent_id': 'local_sales_team'}
                ]
            ),
            
            # Urgency rule
            RoutingRule(
                id="urgent_requests",
                name="Urgent Request Escalation",
                priority=95,
                conditions=[
                    {'field': 'lead.message', 'operator': 'contains', 'value': 'urgent'},
                    {'field': 'lead.message', 'operator': 'contains', 'value': 'asap'}
                ],
                actions=[
                    {'type': 'escalate', 'level': 'high'},
                    {'type': 'notify_immediately', 'channel': 'both'},
                    {'type': 'create_task', 'title': 'URGENT: Lead Follow-up', 'due_hours': 1}
                ]
            ),
            
            # Source-based rule
            RoutingRule(
                id="referral_leads",
                name="Referral Lead Treatment",
                priority=75,
                conditions=[
                    {'field': 'lead.source', 'operator': 'eq', 'value': 'referral'}
                ],
                actions=[
                    {'type': 'tag', 'tag': 'referral'},
                    {'type': 'add_to_sequence', 'sequence': 'referral_nurture'},
                    {'type': 'personalize_message', 'template': 'referral_welcome'}
                ]
            ),
            
            # Industry rule
            RoutingRule(
                id="healthcare_leads",
                name="Healthcare Industry Specialist",
                priority=65,
                conditions=[
                    {'field': 'lead.metadata.industry', 'operator': 'eq', 'value': 'healthcare'}
                ],
                actions=[
                    {'type': 'assign_to', 'agent_id': 'healthcare_specialist'},
                    {'type': 'tag', 'tag': 'healthcare'},
                    {'type': 'customize_content', 'industry': 'healthcare'}
                ]
            ),
            
            # Behavior rule
            RoutingRule(
                id="pricing_page_visitors",
                name="Pricing Page High Intent",
                priority=85,
                conditions=[
                    {'field': 'lead.metadata.landing_page', 'operator': 'contains', 'value': 'pricing'},
                    {'field': 'lead.score_category', 'operator': 'in', 'value': ['hot', 'warm']}
                ],
                actions=[
                    {'type': 'send_message', 'template': 'pricing_inquiry_followup'},
                    {'type': 'offer_call', 'cta': 'Schedule a consultation'},
                    {'type': 'tag', 'tag': 'high_intent'}
                ]
            )
        ]
        
        for rule in default_rules:
            self.rules_engine.add_rule(rule)
    
    def route_lead(self, lead_data: Dict[str, Any],
                  conversation_data: Optional[Dict] = None,
                  available_agents: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Route lead using combined rules + ML + predictive routing.
        
        Returns:
            Routing decision with actions and agent assignment
        """
        result = {
            'lead_id': lead_data.get('id'),
            'timestamp': datetime.now().isoformat(),
            'score': None,
            'score_category': None,
            'matched_rules': [],
            'actions': [],
            'assigned_agent': None,
            'routing_path': []
        }
        
        try:
            # Step 1: ML Scoring
            score, category, importance = self.ml_scorer.score_lead(lead_data)
            result['score'] = score
            result['score_category'] = category
            result['feature_importance'] = importance
            
            # Update lead data with score
            lead_data['score'] = score
            lead_data['score_category'] = category
            
            # Step 2: Evaluate business rules
            matching_rules = self.rules_engine.evaluate_rules(lead_data, conversation_data)
            result['matched_rules'] = [r.id for r in matching_rules]
            
            # Collect all actions from matched rules
            all_actions = []
            for rule in matching_rules:
                all_actions.extend(rule.actions)
            
            # Step 3: Predictive agent routing (if agents available)
            if available_agents:
                agent_id = self.predictive_router.route_lead(lead_data, available_agents)
                if agent_id:
                    result['assigned_agent'] = agent_id
                    all_actions.append({
                        'type': 'assign_to',
                        'agent_id': agent_id,
                        'reason': 'predictive_routing'
                    })
            
            # Step 4: Deduplicate and prioritize actions
            result['actions'] = self._deduplicate_actions(all_actions)
            
            # Step 5: Build routing path
            result['routing_path'] = [
                'ml_scoring',
                'rule_evaluation',
                'predictive_routing' if available_agents else None,
                'action_compilation'
            ]
            result['routing_path'] = [p for p in result['routing_path'] if p]
            
            logger.info(f"Routed lead {result['lead_id']}: score={score}, "
                       f"category={category}, rules={len(matching_rules)}")
            
        except Exception as e:
            logger.error(f"Routing error: {e}")
            result['error'] = str(e)
            # Fallback: basic routing
            result['actions'] = self._fallback_routing(lead_data)
        
        return result
    
    def _deduplicate_actions(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate actions and prioritize."""
        seen = set()
        unique_actions = []
        
        priority_order = [
            'notify_immediately', 'escalate', 'create_task',
            'assign_to', 'add_to_sequence', 'send_message',
            'create_crm_entry', 'tag', 'personalize_message',
            'customize_content', 'offer_call', 'schedule_followup',
            'notify_team'
        ]
        
        # Sort by priority
        def get_priority(action):
            action_type = action.get('type', '')
            try:
                return priority_order.index(action_type)
            except ValueError:
                return len(priority_order)
        
        sorted_actions = sorted(actions, key=get_priority)
        
        for action in sorted_actions:
            action_key = (action.get('type'), action.get('agent_id'), 
                         action.get('sequence'), action.get('tag'))
            
            if action_key not in seen:
                seen.add(action_key)
                unique_actions.append(action)
        
        return unique_actions
    
    def _fallback_routing(self, lead_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback routing when main system fails."""
        category = lead_data.get('score_category', 'cold')
        
        if category == 'hot':
            return [
                {'type': 'notify_immediately', 'channel': 'email'},
                {'type': 'add_to_sequence', 'sequence': 'hot_lead_nurture'},
                {'type': 'create_crm_entry'}
            ]
        elif category == 'warm':
            return [
                {'type': 'add_to_sequence', 'sequence': 'warm_lead_nurture'},
                {'type': 'send_message', 'template': 'warm_lead_welcome'}
            ]
        else:
            return [
                {'type': 'add_to_sequence', 'sequence': 'cold_lead_nurture'}
            ]
    
    def add_custom_rule(self, rule_data: Dict[str, Any]):
        """Add a custom routing rule."""
        rule = RoutingRule(
            id=rule_data.get('id', f"custom_{datetime.now().timestamp()}"),
            name=rule_data.get('name', 'Custom Rule'),
            priority=rule_data.get('priority', 50),
            conditions=rule_data.get('conditions', []),
            actions=rule_data.get('actions', []),
            enabled=rule_data.get('enabled', True)
        )
        self.rules_engine.add_rule(rule)
    
    def get_rules(self) -> List[Dict[str, Any]]:
        """Get all routing rules."""
        return [
            {
                'id': r.id,
                'name': r.name,
                'priority': r.priority,
                'conditions': r.conditions,
                'actions': r.actions,
                'enabled': r.enabled
            }
            for r in self.rules_engine.rules
        ]
    
    def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing rule."""
        for rule in self.rules_engine.rules:
            if rule.id == rule_id:
                for key, value in updates.items():
                    if hasattr(rule, key):
                        setattr(rule, key, value)
                return True
        return False
    
    def delete_rule(self, rule_id: str) -> bool:
        """Delete a routing rule."""
        initial_len = len(self.rules_engine.rules)
        self.rules_engine.rules = [r for r in self.rules_engine.rules if r.id != rule_id]
        return len(self.rules_engine.rules) < initial_len
    
    def train_ml_model(self, leads_data: List[Dict[str, Any]], 
                      labels: List[int]) -> Dict[str, Any]:
        """Train ML model on historical data."""
        return self.ml_scorer.train(leads_data, labels)
    
    def get_ml_feature_importance(self) -> Dict[str, float]:
        """Get ML feature importance."""
        return self.ml_scorer._get_feature_importance(None)


class TimeBasedRouting:
    """Time-based routing logic for business hours."""
    
    def __init__(self, timezone: str = "America/New_York"):
        """Initialize time-based router."""
        self.timezone = timezone
        self.business_hours = {
            'start': time(9, 0),   # 9 AM
            'end': time(17, 0),   # 5 PM
            'days': [0, 1, 2, 3, 4]  # Monday to Friday
        }
        self.after_hours_team: Optional[str] = None
    
    def is_business_hours(self) -> bool:
        """Check if currently within business hours."""
        now = datetime.now()
        
        if now.weekday() not in self.business_hours['days']:
            return False
        
        current_time = now.time()
        return (self.business_hours['start'] <= current_time <= self.business_hours['end'])
    
    def get_next_business_time(self) -> datetime:
        """Get next business hours start time."""
        now = datetime.now()
        
        # If weekend, next Monday
        if now.weekday() >= 5:
            days_until_monday = 7 - now.weekday()
            next_day = now + __import__('datetime').timedelta(days=days_until_monday)
            return next_day.replace(
                hour=self.business_hours['start'].hour,
                minute=self.business_hours['start'].minute,
                second=0
            )
        
        # If after hours, next day
        if now.time() > self.business_hours['end']:
            next_day = now + __import__('datetime').timedelta(days=1)
            return next_day.replace(
                hour=self.business_hours['start'].hour,
                minute=self.business_hours['start'].minute,
                second=0
            )
        
        # If before hours, today
        if now.time() < self.business_hours['start']:
            return now.replace(
                hour=self.business_hours['start'].hour,
                minute=self.business_hours['start'].minute,
                second=0
            )
        
        return now
    
    def get_routing_strategy(self) -> str:
        """Get current routing strategy based on time."""
        if self.is_business_hours():
            return "standard"
        else:
            return "after_hours"
    
    def set_business_hours(self, start: time, end: time, days: List[int]):
        """Set business hours."""
        self.business_hours = {
            'start': start,
            'end': end,
            'days': days
        }


# Convenience functions for common routing patterns
def create_urgency_routing(minutes_since_contact: int) -> List[Dict[str, Any]]:
    """Create urgency-based routing actions."""
    actions = []
    
    if minutes_since_contact < 5:
        actions.append({'type': 'send_acknowledgment', 'delay': 0})
    elif minutes_since_contact < 60:
        actions.append({'type': 'notify_team', 'message': 'Lead waiting 1 hour'})
    elif minutes_since_contact < 240:
        actions.append({'type': 'escalate', 'level': 'medium'})
    else:
        actions.append({'type': 'escalate', 'level': 'high'})
        actions.append({'type': 'notify_manager'})
    
    return actions


def create_follow_up_sequence(lead_category: str, days: int = 14) -> List[Dict[str, Any]]:
    """Create follow-up sequence based on lead category."""
    sequences = {
        'hot': [
            {'day': 0, 'hour': 0, 'action': 'immediate_call'},
            {'day': 1, 'hour': 9, 'action': 'email_follow_up'},
            {'day': 3, 'hour': 10, 'action': 'call_attempt'},
            {'day': 7, 'hour': 9, 'action': 'final_email'},
        ],
        'warm': [
            {'day': 0, 'hour': 2, 'action': 'email_welcome'},
            {'day': 2, 'hour': 9, 'action': 'value_proposition'},
            {'day': 5, 'hour': 10, 'action': 'social_proof'},
            {'day': 10, 'hour': 9, 'action': 'case_study'},
        ],
        'cold': [
            {'day': 0, 'hour': 4, 'action': 'email_welcome'},
            {'day': 3, 'hour': 9, 'action': 'newsletter'},
            {'day': 7, 'hour': 9, 'action': 'educational_content'},
            {'day': 14, 'hour': 9, 'action': 're_engagement'},
        ]
    }
    
    return sequences.get(lead_category, sequences['cold'])