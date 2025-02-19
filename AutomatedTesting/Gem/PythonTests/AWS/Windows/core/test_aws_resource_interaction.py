"""
Copyright (c) Contributors to the Open 3D Engine Project.
For complete copyright and license terms please see the LICENSE at the root of this distribution.

SPDX-License-Identifier: Apache-2.0 OR MIT
"""

import os
import logging
import typing
import shutil

import pytest
import ly_test_tools
import ly_test_tools.log.log_monitor
import ly_test_tools.environment.process_utils as process_utils
import ly_test_tools.o3de.asset_processor_utils as asset_processor_utils

from botocore.exceptions import ClientError
from assetpipeline.ap_fixtures.asset_processor_fixture import asset_processor

AWS_CORE_FEATURE_NAME = 'AWSCore'
AWS_RESOURCE_MAPPING_FILE_NAME = 'default_aws_resource_mappings.json'

process_utils.kill_processes_named("o3de", ignore_extensions=True)  # Kill ProjectManager windows

GAME_LOG_NAME = 'Game.log'

logger = logging.getLogger(__name__)


def setup(launcher: pytest.fixture, asset_processor: pytest.fixture) -> typing.Tuple[pytest.fixture, str]:
    """
    Set up the resource mapping configuration and start the log monitor.
    :param launcher: Client launcher for running the test level.
    :param asset_processor: asset_processor fixture.
    :return log monitor object, metrics file path and the metrics stack name.
    """
    # Create the temporary directory for downloading test file from S3.
    user_dir = os.path.join(launcher.workspace.paths.project(), 'user')
    s3_download_dir = os.path.join(user_dir, 's3_download')
    if not os.path.exists(s3_download_dir):
        os.makedirs(s3_download_dir)

    asset_processor_utils.kill_asset_processor()
    asset_processor.start()
    asset_processor.wait_for_idle()

    file_to_monitor = os.path.join(launcher.workspace.paths.project_log(), GAME_LOG_NAME)
    log_monitor = ly_test_tools.log.log_monitor.LogMonitor(launcher=launcher, log_file_path=file_to_monitor)

    return log_monitor, s3_download_dir


def write_test_data_to_dynamodb_table(resource_mappings: pytest.fixture, aws_utils: pytest.fixture) -> None:
    """
    Write test data to the DynamoDB table created by the CDK application.
    :param resource_mappings: resource_mappings fixture.
    :param aws_utils: aws_utils fixture.
    """
    table_name = resource_mappings.get_resource_name_id("AWSCore.ExampleDynamoTableOutput")
    try:
        aws_utils.client('dynamodb').put_item(
            TableName=table_name,
            Item={
                'id': {
                    'S': 'Item1'
                }
            }
        )
        logger.info(f'Loaded data into table {table_name}')
    except ClientError:
        logger.exception(f'Failed to load data into table {table_name}')
        raise


@pytest.mark.SUITE_periodic
@pytest.mark.usefixtures('automatic_process_killer')
@pytest.mark.usefixtures('asset_processor')
@pytest.mark.usefixtures('cdk')
@pytest.mark.parametrize('feature_name', [AWS_CORE_FEATURE_NAME])
@pytest.mark.parametrize('region_name', ['us-west-2'])
@pytest.mark.parametrize('assume_role_arn', ['arn:aws:iam::645075835648:role/o3de-automation-tests'])
@pytest.mark.parametrize('session_name', ['o3de-Automation-session'])
@pytest.mark.usefixtures('workspace')
@pytest.mark.parametrize('project', ['AutomatedTesting'])
@pytest.mark.parametrize('level', ['AWS/Core'])
@pytest.mark.usefixtures('resource_mappings')
@pytest.mark.parametrize('resource_mappings_filename', [AWS_RESOURCE_MAPPING_FILE_NAME])
@pytest.mark.usefixtures('aws_credentials')
@pytest.mark.parametrize('profile_name', ['AWSAutomationTest'])
@pytest.mark.usefixtures('cdk')
@pytest.mark.parametrize('deployment_params', [['--all']])
@pytest.mark.parametrize('destroy_stacks_on_teardown', [True])
class TestAWSCoreAWSResourceInteraction(object):
    """
    Test class to verify the scripting behavior for the AWSCore gem.
    """

    @pytest.mark.parametrize('expected_lines', [
        ['(Script) - [S3] Head object request is done',
         '(Script) - [S3] Head object success: Object example.txt is found.',
         '(Script) - [S3] Get object success: Object example.txt is downloaded.',
         '(Script) - [Lambda] Completed Invoke',
         '(Script) - [Lambda] Invoke success: {"statusCode": 200, "body": {}}',
         '(Script) - [DynamoDB] Results finished']])
    @pytest.mark.parametrize('unexpected_lines', [
        ['(Script) - [S3] Head object error: No response body.',
         '(Script) - [S3] Get object error: Request validation failed, output file directory doesn\'t exist.',
         '(Script) - Request validation failed, output file miss full path.',
         '(Script) - ']])
    def test_scripting_behavior(self,
                                level: str,
                                launcher: pytest.fixture,
                                workspace: pytest.fixture,
                                asset_processor: pytest.fixture,
                                resource_mappings: pytest.fixture,
                                aws_utils: pytest.fixture,
                                expected_lines: typing.List[str],
                                unexpected_lines: typing.List[str]):
        """
        Setup: Deploys cdk and updates resource mapping file.
        Tests: Interact with AWS S3, DynamoDB and Lambda services.
        Verification: Script canvas nodes can communicate with AWS services successfully.
        """

        log_monitor, s3_download_dir = setup(launcher, asset_processor)
        write_test_data_to_dynamodb_table(resource_mappings, aws_utils)

        launcher.args = ['+LoadLevel', level]
        launcher.args.extend(['-rhi=null'])

        with launcher.start(launch_ap=False):
            result = log_monitor.monitor_log_for_lines(
                expected_lines=expected_lines,
                unexpected_lines=unexpected_lines,
                halt_on_unexpected=True
                )

            assert result, "Expected lines weren't found."

        assert os.path.exists(os.path.join(s3_download_dir, 'output.txt')), \
            'The expected file wasn\'t successfully downloaded.'
        # clean up the file directories.
        shutil.rmtree(s3_download_dir)
