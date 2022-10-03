import media
import os
import requests

direct = os.path.split(os.path.split(__file__)[0])[0]
output_folder = os.path.join(direct, 'Outputs')

# collect all media
all_url = f'https://mediadive.dsmz.de/rest/media'
medias = requests.get(all_url).json()['data']
print(len(medias))

count = 1
for med in medias:
    print(count, med['id'])

    output_path = os.path.join(output_folder,  f'{med["id"]}.xml')
    
    media.create(output_path, med['id'])

    count += 1




