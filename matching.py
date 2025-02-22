import json

hr_requirements = {
    'technical_skills': ['Python', 'SQL'],
    'soft_skills': ['Problem-solving abilities', 'Teamwork'],
    'additional_skills': ['Adaptability', 'Openness to learning new technologies'],
    'red_flags': ['Lack of accountability'],
    'minimum_experience': ['2-3 years']
}

def load_candidate_json(candidate_json_path):
    with open(candidate_json_path, 'r') as file:
        return json.load(file)

def compare_json(candidate_json, hr_json):
    score = 0
    detailed_results = {
        'matched_technical_skills': [],
        'matched_soft_skills': [],
        'matched_additional_skills': [],
        'red_flags_found': [],
        'extra_skills': [],
        'experience_match': False
    }

    # Weights for scoring
    weights = {
        'technical_skills': 5,
        'soft_skills': 3,
        'additional_skills': 2,
        'extra_skills': 1,
        'red_flags': -10
    }

    candidate_skills = candidate_json.get('Skills', [])

    for skill in candidate_skills:
        if skill in hr_json['technical_skills']:
            score += weights['technical_skills']
            detailed_results['matched_technical_skills'].append(skill)
        elif skill in hr_json['additional_skills']:
            score += weights['additional_skills']
            detailed_results['matched_additional_skills'].append(skill)
        else:
            score += weights['extra_skills']
            detailed_results['extra_skills'].append(skill)

    inferred_soft_skills = []
    for exp in candidate_json.get('Experience', []):
        desc = exp.get('Description', '').lower()
        if 'team' in desc or 'collaborate' in desc:
            inferred_soft_skills.append('Teamwork')
        if 'problem' in desc or 'solve' in desc:
            inferred_soft_skills.append('Problem-solving abilities')

    for soft_skill in set(inferred_soft_skills):
        if soft_skill in hr_json['soft_skills']:
            score += weights['soft_skills']
            detailed_results['matched_soft_skills'].append(soft_skill)

    for flag in hr_json['red_flags']:
        if flag.lower() in candidate_json.get('Everything Else', '').lower():
            score += weights['red_flags']
            detailed_results['red_flags_found'].append(flag)

    total_experience = sum(exp.get('Months', 0) for exp in candidate_json.get('Experience', []))
    required_exp_years = int(hr_json['minimum_experience'][0].split('-')[0]) * 12

    if total_experience >= required_exp_years:
        score += 5  # Weight for matching experience
        detailed_results['experience_match'] = True

    return score, detailed_results

candidate_json_path = r"D:\Capstone\parsed_resumes\Sanjana_Maini.json"
candidate_json = load_candidate_json(candidate_json_path)

final_score, results = compare_json(candidate_json, hr_requirements)

print("Candidate Score:", final_score)
print("Detailed Comparison:", json.dumps(results, indent=2))
