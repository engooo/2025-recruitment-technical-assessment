from dataclasses import dataclass
from typing import List, Dict, Union
from flask import Flask, request, jsonify
import re
import sys
# ==== Type Definitions, feel free to add or modify ===========================
@dataclass
class CookbookEntry:
	name: str

@dataclass
class RequiredItem():
	name: str
	quantity: int

@dataclass
class Recipe(CookbookEntry):
	required_items: List[RequiredItem]

@dataclass
class Ingredient(CookbookEntry):
	cook_time: int


# =============================================================================
# ==== HTTP Endpoint Stubs ====================================================
# =============================================================================
app = Flask(__name__)

# Store your recipes here!
cookbook = []

# Task 1 helper (don't touch)
@app.route("/parse", methods=['POST'])
def parse():
	data = request.get_json()
	recipe_name = data.get('input', '')
	parsed_name = parse_handwriting(recipe_name)
	if parsed_name is None:
		return 'Invalid recipe name', 400
	return jsonify({'msg': parsed_name}), 200

# [TASK 1] ====================================================================
# Takes in a recipeName and returns it in a form that 
def parse_handwriting(recipeName: str) -> Union[str | None]:
	recipeName = re.sub(r'-', ' ', recipeName)
	recipeName = re.sub(r'_', ' ', recipeName)
	recipeName = re.sub(r'[^a-zA-Z\s]', '', recipeName)
	recipeName = recipeName.title()
	recipeName = re.sub(r'\s+', ' ', recipeName.strip())
	
	if len(recipeName) <= 0:
		return None

	return recipeName


# [TASK 2] ====================================================================
# Endpoint that adds a CookbookEntry to your magical cookbook
@app.route('/entry', methods=['POST'])
def create_entry():
	data = request.get_json()

	entry_type = data.get('type')
	name = data.get('name')

	if entry_type not in ['recipe', 'ingredient']:
		return 'Invalid type', 400
	
	# check unique cookbook entries
	for entry in cookbook:
		if entry.name == name:
			return 'Name is not unique', 400
		
	if entry_type == 'recipe':
		# check unique required items
		req_items = set()
		for item in data.get('requiredItems'):
			item_name = item.get('name')
			if item_name in req_items:
				return 'Required item name is not unique', 400
			req_items.add(item_name)
		
		required_items = [RequiredItem(name=item['name'], quantity=item['quantity']) for item in data.get('requiredItems')]
		entry = Recipe(name=name, required_items=required_items)

	elif entry_type == 'ingredient':
		cookTime = data.get('cookTime')
		if cookTime < 0:
			return 'Invalid cook time', 400
		entry = Ingredient(name=name, cook_time=cookTime)
	
	cookbook.append(entry)
	return 'success!', 200


# [TASK 3] ====================================================================
# A helper function to recursively gather ingredients and calculate cook time
def get_ingredients_and_time(required_items):
	ingredients = []
	total_cook_time = 0

	for item in required_items:
		if isinstance(item, Recipe):
			if not any(entry.name == item.name for entry in cookbook if isinstance(entry, Recipe)):
				return None, None
			nested_ingredients, nested_cook_time = get_ingredients_and_time(item.required_items)
			for nested_item in nested_ingredients:
				ingredients.append({
					'name': nested_item['name'],
					'quantity': nested_item['quantity'] * item.quantity
				})
			total_cook_time += nested_cook_time * item.quantity
		elif isinstance(item, Ingredient):
			if not any(entry.name == item.name for entry in cookbook if isinstance(entry, Ingredient)):
				print("POOPOOCACA")
				return None, 'Ingredient not in cookbook', 400
			ingredients.append({'name': item.name, 'quantity': item.quantity})
			total_cook_time += item.cook_time * item.quantity

	return ingredients, total_cook_time

# Endpoint that returns a summary of a recipe that corresponds to a query name
@app.route('/summary', methods=['GET'])
def summary():
    recipe_name = request.args.get('name')

    recipe = next((entry for entry in cookbook if isinstance(entry, Recipe) and entry.name == recipe_name), None)
    
    if not recipe:
        return 'Recipe aint here', 400
    ingredients, cook_time = get_ingredients_and_time(recipe.required_items)
    if not ingredients:
       return 'recipe no here', 400
		
    return jsonify({
        'name': recipe.name,
        'cookTime': cook_time,
        'ingredients': ingredients
    }), 200
	



# =============================================================================
# ==== DO NOT TOUCH ===========================================================
# =============================================================================

if __name__ == '__main__':
	parse_handwriting("    Riz@z  RISO00tto!   ")
	
	app.run(debug=True, port=8080)
