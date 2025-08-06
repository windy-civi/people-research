My goal with this project is to make a Github Action scraper that clones @https://github.com/openstates/people , follows the directory structure, loops through active legislators in each locale  found under `data/$LOCALE/legislature/$NAME-$UUID.yml, and copy the directory structure, but use the yaml files to output json that uses Claude Deep 
Research to look up the following:
- each representative's campaign website and find their issues, outputting it as an array of issues with title/description
- each represenatives top donors by industry/single-issue/corporation, outputted also as an array with the donor name, potential issue they care about, and money donated.

The outputted file should match the folder structure of openstates/people, but output as $NAME-$UUID.research.json.

it should use python, and the python files should not be in the yml script