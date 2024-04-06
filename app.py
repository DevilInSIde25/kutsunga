from flask import request, jsonify, Response, abort
from flask_api import FlaskAPI
from flasgger import Swagger, swag_from
from report_racing_vasiliy import build_report, print_report
from constants import FILES
from itertools import product
import xml.etree.ElementTree as ET

app = FlaskAPI(__name__)
swagger = Swagger(app)


def get_report(sort=None, driver_name=None):
    """
    This function generates a report for all drivers or a single driver if driver_name is specified.

    :param sort: The order in which to sort the drivers. Acceptable values are 'asc' or 'desc'.
    :param driver_name: The name of the driver to filter by. If specified, the report will only contain
        information about this driver.
    :return: A dictionary containing the report information.
    """
    race_result = build_report(FILES / 'start.log', FILES / 'end.log', sort=sort)
    report_result = print_report(FILES / 'abbreviations.txt', race_result, driver_name=driver_name)
    return report_result


@app.route('/')
@app.route('/api/v1/report/', methods=['GET'])
@swag_from('swagger/report.yml')
def report():
    """
    This endpoint generates a report of all drivers or a single driver if driver_id is specified.

    :return: A JSON or XML response containing the report data.
    """
    report_format = request.args.get('format')
    sort = request.args.get('order')
    report_result = get_report(sort=sort)

    response_formats = {
        'json': lambda: jsonify([{'name': driver, 'team': data[0], 'result': data[1]}
                                 for driver, data in report_result.items()]),
        'xml': lambda: Response(report_to_xml(report_result), content_type='application/xml')
    }
    if report_format in response_formats:
        return response_formats[report_format]()
    else:
        abort(400, 'Unsupported format')


def report_to_xml(report_result):
    """
    This function converts a report dictionary to an XML string.

    :param report_result: The report dictionary.
    :return: An XML string representing the report.
    """
    root = ET.Element('report')
    for driver, data in report_result.items():
        driver_element = ET.SubElement(root, 'driver')
        name_element = ET.SubElement(driver_element, 'name')
        name_element.text = driver
        team_element = ET.SubElement(driver_element, 'team')
        team_element.text = data[0]
        result_element = ET.SubElement(driver_element, 'result')
        result_element.text = str(data[1])
    xml_string = ET.tostring(root, encoding='utf8', method='xml')
    return xml_string


@app.route('/api/v1/report/drivers/', methods=['GET'])
@swag_from('swagger/drivers.yml')
def drivers():
    """
    This endpoint returns a list of all drivers or a single driver if driver_id is specified.

    :return: A JSON or XML response containing the driver data.
    """
    report_format = request.args.get('format')
    sort = request.args.get('order')
    driver_id = request.args.get("driver_id")
    race_result = build_report(FILES / 'start.log', FILES / 'end.log', sort=sort)
    report_result = get_report(sort=sort)
    driver_info = {}

    results_product = product(race_result.items(), report_result.items())
    for ((driver_code, time_result), (driver_name, race_data)) in results_product:
        if time_result == race_data[1]:
            driver_info[driver_name] = driver_code

    if driver_id:
        filtered_results = filter(lambda data: data[1] == driver_id, driver_info.items())
        driver_name = next(filtered_results, None)
        if driver_name:
            report_result = get_report(driver_name=driver_name[0])
            response_formats = {
                'json': lambda: jsonify([{'name': driver, 'team': data[0], 'result': data[1]}
                                 for driver, data in report_result.items()]),
                'xml': lambda: Response(report_to_xml(report_result), content_type='application/xml')
            }
            if report_format in response_formats:
                return response_formats[report_format]()
            else:
                abort(400, 'Unsupported format')
        else:
            abort(404, 'Driver not found')
    else:
        response_formats = {
            'json': lambda: jsonify([{'name': driver, 'id': data}
                                 for driver, data in driver_info.items()]),
            'xml': lambda: Response(drivers_to_xml(driver_info), content_type='application/xml')
        }
        if report_format in response_formats:
            return response_formats[report_format]()
        else:
            abort(400, 'Unsupported format')


def drivers_to_xml(data):
    root = ET.Element('report')
    for driver, driver_id in data.items():
        driver_element = ET.SubElement(root, 'driver')
        name_element = ET.SubElement(driver_element, 'name')
        name_element.text = driver
        id_element = ET.SubElement(driver_element, 'id')
        id_element.text = driver_id
    xml_string = ET.tostring(root, encoding='utf8', method='xml')
    return xml_string


if __name__ == '__main__':
    app.run(debug=True)
