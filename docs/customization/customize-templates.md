# Customizing RDF Differ Templates

## Adding a new Application Profile template

For adding a new Application Profile (AP) create a new folder under [resources/templates](resources/templates) with the name
of your new AP, following the structure explained below.

Folder structure needed for adding a new AP:

```text
resources/templates
│   
└───<new_application_profile>
│   │
│   └───queries          <--- folder that contains SPARQL queries
│   │    │   query1.rq
│   │    │   query2.rq
│   │    │   ...
│   │    
│   └───template_variants
│       │
│       └───html        <--- folder that contains files needed for a html template
│       │
│       │  
│       └───json        <--- folder that contains files needed for a json template
```

### HTML template variant

#### HTML folder structure

```text
html                 <--- the template_variants subfolder 
│
└───config.json      <--- configuration file
│   
└───templates        <--- this is the folder that contains the jinja html templates
   │
   │  file1.html
   │  file2.html
   │  main.html

```

_Note_ Make sure that in the templates folder there is an entrypoint file named the same as the one defined in the config.json file (i.e `"template": "main.html"`)

#### HTML template structure

The HTML template is built be combining four major parts as layout, main, macros and sections. The layout file (layout.html)
will have the rules of how the report will look like in terms of positioning and styling. Macros will contain all the
jinja2 macros used across the template. A section represents the result of a query that was run with additional html and
will be used to build the report.
As the name suggest the main file of the html template is main.html. Here is where every other file that are a different
section in the report are included and will form the HTML report.

Example of including a section in the main html file:

`{% include "conceptscheme/added_instance_concept_scheme.html" with context %}`

Each section file has one or more variables where the SPARQL query result is saved
as a pandas dataframe.

Example

`{% set content, error = from_endpoint(conf.default_endpoint).with_query_from_file(conf.query_files["added_instance_concept.rq"]).fetch_tabular() %})`

_Note_ The system has in place an autodiscover process for the SPARQL queries in the queries folder. Make sure that the file
name added for the variable above (`added_instance_concept.rq`) exists in the queries folder.

### Adjusting an existing HTML template

#### Adding a new query/section

To add a query a new file needs to be created and added into the queries folder as the system will autodiscover
this. After this is done a new html file that will represent a new section needs to be created. The content of this is
similar to the existing ones and the only thing that needs to be adjusted will be the query file name in the content
variable definition as presented below:

```python
{% set content, error = from_endpoint(conf.default_endpoint).with_query_from_file(conf.query_files["new_query_file.rq"]).fetch_tabular() %})
```

As a final step, the created html file needs to be included in the report and to do this it has to be included in the
main.html file by using the include block.

```python
       --- relative path to the new html path
      {% include "conceptscheme/labels/new file name.html" with context %}
```

For adding a count query that will be used in the statistics
section the steps are a bit different. First, will need to add the new query file following the naming conventions and
adding the prefix count_ to the file name in queries folder. After this, the statistics.html will need to be modified as follows:

1. Create a new row in the existing table by using `<tr>` tag.
2. Create the necessary columns for the newly created row. Each row should have 7 values as this is the defined table
structure (Property group, Property ,Added, Deleted, Updated, Moved, Changed) and each of them should be included by
using a `<td>` tag if you are not using the block below to autogenerate this.

```python
    {% set content, error = from_endpoint(conf.default_endpoint).with_query_from_file(conf.query_files["new_count_query_file_name.rq"]).fetch_tabular() %}
    
    {% call mc.render_fetch_results(content, error) %}

    {{ mc.count_value(content) }}
    {% endcall %}
```

_Note_ The order of the cells is important. If you don't want to include a type of operation just create a `<td>` with a
desired value (i.e `<td>N/A</td>`). To avoid confusions, count queries should be added for all type of operations.
The example below will show how to add a complete row in the statistics section of the report

```python
<tr>
    <td>Name of the property group</td>
    <td>Name of the property</td>
    --- this will bring the number generated from the SPARQL query for added occurences and will create the <td> tag
        {% set content, error = from_endpoint(conf.default_endpoint).with_query_from_file(conf.query_files["count_added_property_concept_scheme_pref_label.rq"]).fetch_tabular() %}
        
        {% call mc.render_fetch_results(content, error) %}

        {{ mc.count_value(content) }}
        {% endcall %}
        
    --- this will bring the number generated from the SPARQL query for deleted occurences and will create the <td> tag
        {% set content, error = from_endpoint(conf.default_endpoint).with_query_from_file(conf.query_files["count_deleted_property_concept_scheme_pref_label.rq"]).fetch_tabular() %}
        
        {% call mc.render_fetch_results(content, error) %}

        {{ mc.count_value(content) }}
        {% endcall %}
        
    --- this will bring the number generated from the SPARQL query for updated occurences and will create the <td> tag
        {% set content, error = from_endpoint(conf.default_endpoint).with_query_from_file(conf.query_files["count_updated_property_concept_scheme_pref_label.rq"]).fetch_tabular() %}
        
        {% call mc.render_fetch_results(content, error) %}

        {{ mc.count_value(content) }}
        {% endcall %}
        
    --- this will bring the number generated from the SPARQL query for moved occurences and will create the <td> tag
        {% set content, error = from_endpoint(conf.default_endpoint).with_query_from_file(conf.query_files["count_moved_property_concept_scheme_pref_label.rq"]).fetch_tabular() %}
        
        {% call mc.render_fetch_results(content, error) %}

        {{ mc.count_value(content) }}
        {% endcall %}
        
    --- this will bring the number generated from the SPARQL query for changed occurences and will create the <td> tag
        {% set content, error = from_endpoint(conf.default_endpoint).with_query_from_file(conf.query_files["count_changed_property_concept_scheme_pref_label.rq"]).fetch_tabular() %}
        
        {% call mc.render_fetch_results(content, error) %}

        {{ mc.count_value(content) }}
        {% endcall %}

</tr>
```

#### Removing a query/section from HTML

To remove a section from the existing report you just need to delete or comment the include statement from the main.html
file. If you decide to delete the include statement it's recommended to delete the query from the queries folder to avoid
confusions later on.

```python
            {% include "conceptscheme/labels/added_property_concept_scheme_pref_label.html" with context %}
```

To remove a row from the statistics section just delete or comment the `<tr>` bloc from the statistics.html file

```python
<tr>
    <td>Labels</td>
    <td>skos:prefLabel</td>
    
        {% set content, error = from_endpoint(conf.default_endpoint).with_query_from_file(conf.query_files["count_added_property_concept_scheme_pref_label.rq"]).fetch_tabular() %}
        
        {% call mc.render_fetch_results(content, error) %}

        {{ mc.count_value(content) }}
        {% endcall %}
        
    
        {% set content, error = from_endpoint(conf.default_endpoint).with_query_from_file(conf.query_files["count_deleted_property_concept_scheme_pref_label.rq"]).fetch_tabular() %}
        
        {% call mc.render_fetch_results(content, error) %}

        {{ mc.count_value(content) }}
        {% endcall %}
        
    
        {% set content, error = from_endpoint(conf.default_endpoint).with_query_from_file(conf.query_files["count_updated_property_concept_scheme_pref_label.rq"]).fetch_tabular() %}
        
        {% call mc.render_fetch_results(content, error) %}

        {{ mc.count_value(content) }}
        {% endcall %}
        
    
        {% set content, error = from_endpoint(conf.default_endpoint).with_query_from_file(conf.query_files["count_moved_property_concept_scheme_pref_label.rq"]).fetch_tabular() %}
        
        {% call mc.render_fetch_results(content, error) %}

        {{ mc.count_value(content) }}
        {% endcall %}
        
    
        {% set content, error = from_endpoint(conf.default_endpoint).with_query_from_file(conf.query_files["count_changed_property_concept_scheme_pref_label.rq"]).fetch_tabular() %}
        
        {% call mc.render_fetch_results(content, error) %}

        {{ mc.count_value(content) }}
        {% endcall %}
        
    
</tr>
```

### JSON template variant

#### JSON folder structure

```text
json                 <--- the template_variants subfolder
│
└───config.json      <--- configuration file
│   
└───templates        <--- this is the folder that contains the jinja json templates
   │
   │  main.json

```

_Note_ Make sure that in the templates folder there is an entrypoint file named the same as the one defined in the config.json file (i.e `"template": "main.json"`)

### JSON template structure

The JSON report is automatically built by running all queries that are found in the queries folder as the system has
autodiscover process for this. In the beginning of this report there will be 3 keys that will show the metadata of the
report like dataset used, created time and application profile used.  Each query result can be identified in the report
by the filename and will contain a results key that will represent the result set brought back by the query

```json
{
   //--- Metadata
   
    "dataset_name": "name of dataset",
    "timestamp": "time",
    "application_profile": "application profile namme",
    
    //--- Query result set
    
    "count_changed_property_concept_definition.rq":
    {
        "head":
        {
            "vars":
            [
                "entries"
            ]
        },
        "results":
        {
            "bindings":
            [
                {
                    "entries":
                    {
                        "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                        "type": "literal",
                        "value": "0"
                    }
                }
            ]
        }
    }
}
```

### Adjusting an existing JSON template

#### Removing a query/section from JSON

To remove a query result set from the report simply remove the query from the queries folder.

> **NOTE:** Doing this will also affect the html template and it's recommended to adjust the html template, if this exists as a template variant for the application profile that you are working with, following the instruction above to avoid errors when generating the hmtl template variant.
