import json, re
from typing import Optional
from .links import shopping_links
from ..config import settings
from ..models import HomeBudgetInput, PartyBudgetInput, JewelryBudgetInput

try:
    from google import genai
    from google.genai import types
except Exception:
    genai = None
    types = None


def _extract_json(text: str):
    text = text.strip()
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.I)
    text = re.sub(r'\s*```$', '', text)
    start = text.find('{'); end = text.rfind('}')
    if start >= 0 and end > start:
        text = text[start:end+1]
    return json.loads(text)


def _fallback_home(x):
    b=x.total_budget
    alloc={'Lighting':round(b*.25,2),'Furniture':round(b*.45,2),'Fans':round(b*.12,2),'Dining':round(b*.10,2),'Reserve':round(b*.08,2)}
    items=[]
    if x.num_lights: items.append({'name':'Energy-efficient LED bulbs','description':f'{x.num_lights} warm-white LED bulbs for general lighting.','estimated_price':round(alloc['Lighting']*.45,2),'quantity':x.num_lights,'search_terms':'warm white LED bulbs India'})
    if x.num_fans: items.append({'name':'Ceiling fans','description':f'Energy-efficient ceiling fans for the selected rooms.','estimated_price':round(alloc['Fans'],2),'quantity':x.num_fans,'search_terms':'energy efficient ceiling fan India'})
    if x.num_furniture: items.append({'name':'Practical furniture set','description':'Space-efficient furniture selected around the available allocation.','estimated_price':round(alloc['Furniture'],2),'quantity':x.num_furniture,'search_terms':'modern affordable furniture India'})
    if x.num_dining_tables: items.append({'name':'Compact dining table','description':'Simple durable dining table suitable for a home interior.','estimated_price':round(alloc['Dining'],2),'quantity':x.num_dining_tables,'search_terms':'compact dining table India'})
    remaining=round(b-sum(i['estimated_price'] for i in items),2)
    return {'mode':'demo','total_budget':b,'budget_breakdown':[{'category':k,'allocation':v} for k,v in alloc.items()], 'items':items,'remaining_budget':max(0,remaining),'additional_suggestions':['Compare multiple sellers before buying.','Prioritize essential items and postpone non-essential purchases.','Consider used furniture where appropriate for additional savings.']}

def _fallback_party(x):
    b=x.total_budget
    cats=[('Venue',.25),('Catering',.35),('Decorations',.15),('Entertainment',.12),('Contingency',.13)]
    breakdown=[{'category':n,'allocation':round(b*p,2)} for n,p in cats]
    items=[{'name':n,'description':f'Budget allocation for {n.lower()} for a {x.party_type.lower()} event.','estimated_price':a,'quantity':1,'search_terms':f'{x.party_type} {n} Chennai'} for n,a in breakdown]
    return {'mode':'demo','total_budget':b,'party_type':x.party_type,'guests':x.num_guests,'budget_breakdown':breakdown,'items':items,'venue_suggestions':[{'name':'Local event venue','estimated_price':breakdown[0]['allocation'],'search_terms':f'{x.venue_type} party venue Chennai'}],'remaining_budget':0,'additional_suggestions':['Confirm venue inclusions before paying.','Get per-person catering quotes.','Keep a contingency reserve for last-minute expenses.']}

def _fallback_jewelry(x, image_name=None):
    b=x.total_budget
    recs=[('Statement earrings',.28,'statement earrings Indian occasion'),('Delicate necklace',.38,'delicate necklace Indian jewellery'),('Bracelet or bangles',.18,'bracelet bangles Indian jewellery')]
    items=[{'name':n,'description':'Versatile Indian-friendly styling option.','estimated_price':round(b*p,2),'search_terms':q} for n,p,q in recs]
    return {'mode':'demo','outfit_analysis':{'colors':['not analyzed without live vision model'],'style':'versatile','formality':'occasion-ready'} if image_name else None,'total_budget':b,'jewelry_recommendations':items,'remaining_budget':round(b-sum(i['estimated_price'] for i in items),2),'styling_tips':['Match metal tone with the outfit details.','Keep statement pieces balanced with neckline and overall formality.','Compare hallmarking, purity and return policies before purchasing.']}

async def _gemini(prompt: str, image_bytes: Optional[bytes]=None):
    if not settings.gemini_api_key or genai is None:
        return None
    client=genai.Client(api_key=settings.gemini_api_key)
    contents=[prompt]
    if image_bytes:
        contents.append(types.Part.from_bytes(data=image_bytes, mime_type='image/jpeg'))
    response=client.models.generate_content(model=settings.gemini_model, contents=contents, config=types.GenerateContentConfig(response_mime_type='application/json', temperature=0.3))
    return _extract_json(response.text)

async def home(x):
    prompt=f'''Create an India-specific home interior budget plan in strict JSON. Budget INR {x.total_budget}. Rooms: {x.rooms}. Lights: {x.num_lights}. Fans: {x.num_fans}. Furniture pieces: {x.num_furniture}. Dining tables: {x.num_dining_tables}. Requirements: {x.requirements or 'none'}.
Schema: {{"total_budget":0,"budget_breakdown":[{{"category":"","allocation":0}}],"items":[{{"name":"","description":"","estimated_price":0,"quantity":1,"search_terms":""}}],"remaining_budget":0,"additional_suggestions":[]}}. Keep total allocations and item estimates within budget.''' 
    result=await _gemini(prompt)
    return result or _fallback_home(x)

async def party(x):
    prompt=f'''Create an India-specific party budget plan in strict JSON. Budget INR {x.total_budget}; party type {x.party_type}; venue {x.venue_type}; guests {x.num_guests}; needs {x.needs}; requirements {x.requirements or 'none'}.
Schema: {{"total_budget":0,"party_type":"","guests":0,"budget_breakdown":[{{"category":"","allocation":0}}],"items":[{{"name":"","description":"","estimated_price":0,"quantity":1,"search_terms":""}}],"venue_suggestions":[{{"name":"","estimated_price":0,"search_terms":""}}],"remaining_budget":0,"additional_suggestions":[]}}''' 
    result=await _gemini(prompt)
    return result or _fallback_party(x)

async def jewelry(x, image_bytes=None, image_name=None):
    prompt=f'''Create India-specific jewelry recommendations in strict JSON. Total budget INR {x.total_budget}; occasion {x.occasion}; preferences {x.preferences or 'none'}. If an outfit image is attached, analyze its colors, style and formality. Recommend jewelry that complements it. Prices must remain within budget.
Schema: {{"outfit_analysis":{{"colors":[],"style":"","formality":""}},"total_budget":0,"jewelry_recommendations":[{{"name":"","description":"","estimated_price":0,"search_terms":""}}],"remaining_budget":0,"styling_tips":[]}}'''
    result=await _gemini(prompt, image_bytes)
    return result or _fallback_jewelry(x, image_name)

def add_links(result, kind):
    collection = result.get('items', []) if kind in ('home','party') else result.get('jewelry_recommendations', [])
    for item in collection:
        terms=item.get('search_terms','')
        item['shopping_links']=shopping_links(terms, kind) if terms else {}
    if kind=='party':
        for item in result.get('venue_suggestions',[]):
            item['search_links']=shopping_links(item.get('search_terms',''),'party')
    return result
