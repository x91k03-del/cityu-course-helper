"""Apply explicit section restrictions, including non-business-college sections."""
def compatible(section,profile):
    major=profile['programme'];actual_major='CM' if major=='CM' else 'CSC1'
    for r in section['restrictions']:
        value={'major':actual_major,'programme':profile.get('programme_code'),'cohort':str(profile.get('cohort','')),
            'college':profile.get('college'),'degree':profile.get('degree')}.get(r['field'])
        if r['field']=='college' and set(r['values'])=={'CB'} and value is None and major in ('CM','CS'):
            # Mathematics/Computing programmes belong outside the College of Business;
            # no unverified internal code for their own colleges is invented.
            member=False
        elif value is None or value=='':return False
        else:member=value in r['values']
        if member!=(r['mode']=='only'):return False
    return True

def preferred(sections,profile):
    eligible=[s for s in sections if compatible(s,profile)]
    major='CM' if profile['programme']=='CM' else 'CSC1'
    dedicated=[s for s in eligible if any(r['field']=='major' and r['mode']=='only' and major in r['values'] for r in s['restrictions'])]
    return dedicated or eligible
