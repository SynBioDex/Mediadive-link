import requests
import sbol3
import helper  # local function


def create(output_path, media_id):
    # initialise sbol doc
    doc = sbol3.Document()
    namespace_url = 'https://mediadive.dsmz.de/'
    doc.addNamespace(namespace_url, 'mediadive')

    # initialise unit dictionary
    # https://www.ebi.ac.uk/ols/ontologies/uo/terms?iri=http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FUO_0000098
    ontology_of_measures = {'ml':'http://purl.obolibrary.org/obo/UO_0000098',
                            'g':'http://purl.obolibrary.org/obo/UO_0000021',
                            'g/l': 'http://purl.obolibrary.org/obo/UO_0000175',
                            'mg': 'http://purl.obolibrary.org/obo/UO_0000022',
                            '%': 'http://purl.obolibrary.org/obo/UO_0000187'}

    # collect media info
    url = f'https://mediadive.dsmz.de/rest/medium/{media_id}'
    media_dict = requests.get(url).json()['data']
    m_name = media_dict['medium']['name']
    
    # create media component
    media = sbol3.Component(helper.check_name(m_name), name=m_name, types='http://purl.obolibrary.org/obo/NCIT_C48164')  # ncit c48164 is a medium
    setattr(media, 'place_holder', sbol3.TextProperty(media, f'{namespace_url}id', '0', '*', initial_value=str(f'https://mediadive.dsmz.de/medium/{media_dict["medium"]["id"]}')))
    for key in ['complex_medium', 'min_pH', 'max_pH', 'source', 'link']:
        if key in media_dict['medium']:
            setattr(media, 'place_holder', sbol3.TextProperty(media, f'{namespace_url}{key}', '0', '*', initial_value=str(media_dict['medium'][key])))

    # create externally defined solutions and their measures
    sols = media_dict['solutions']
    for sol in sols:
        sol_name = sol['name']

        # checks that only creating main solution not other used solutions
        if 'Main' in sol_name:
            recipe = sol['recipe']
            for ing in recipe:
                if 'compound' in ing:
                    ing_id = ing['compound_id']

                    # collect information about single ingredient
                    url = f'https://mediadive.dsmz.de/rest/ingredient/{ing_id}'
                    ing_dict = requests.get(url).json()['data']
                    

                    # set defined as via Pubchem, Chebi, or if it doesn't exist via media dive
                    # if ing_dict["ChEBI"] is not None:
                    #     definition = f'https://pubchem.ncbi.nlm.nih.gov/compound/{ing_dict["ChEBI"]}'
                    #     chebi_exists = True
                    if ing_dict["ChEBI"] is not None:
                        definition = f'https://identifiers.org/CHEBI:{ing_dict["ChEBI"]}'
                        chebi_exists = True
                    else:
                        definition = f'https://mediadive.dsmz.de/ingredients/{ing_dict["id"]}?'
                        chebi_exists = False

                    # create measure
                    measure = sbol3.Measure(value=ing['amount'], unit=ontology_of_measures[ing['unit']])

                    # create ingredient
                    types = ['https://identifiers.org/SBO:0000247']  # simple chemical
                    extchem = sbol3.ExternallyDefined(types, definition, name=ing_dict['name'], measures=[measure])

                    # add ingredient properties
                    for key in ['id', 'CAS-RN', 'mass','formula','density']:
                        if key == 'id' and not chebi_exists:
                            pass
                        else:
                            if ing_dict[key] is not None:
                                setattr(extchem, key, sbol3.TextProperty(extchem, f'{namespace_url}{key}', '0', '*', initial_value=str(ing_dict[key])))
                    for key in ['recipe_order', 'optional']:
                        setattr(extchem, key, sbol3.TextProperty(extchem, f'{namespace_url}{key}', '0', '*', initial_value=str(ing[key])))
                    
                    # add ingredient to media
                    media.features.append(extchem)
                else:
                    # create solution
                    types = ['http://purl.obolibrary.org/obo/NCIT_C70830']
                    definition = f'https://mediadive.dsmz.de/solutions/{ing["solution_id"]}'
                    measure = sbol3.Measure(value=ing['amount'], unit=ontology_of_measures[ing['unit']])
                    extchem = sbol3.ExternallyDefined(types, definition, name=ing['solution'], measures=[measure])
                    for key in ['recipe_order', 'optional']:
                        setattr(extchem, key, sbol3.TextProperty(extchem, f'{namespace_url}{key}', '0', '*', initial_value=str(ing[key])))

                    # add solution to media
                    media.features.append(extchem)

    # add media to sbol doc
    doc.add(media)
    doc.write(output_path)

    return
    

    