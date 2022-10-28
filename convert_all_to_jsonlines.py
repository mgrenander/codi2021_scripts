import argparse
import helper
from os.path import join
import logging

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
                    datefmt='%m/%d/%Y %H:%M:%S',
                    level=logging.INFO)
logger = logging.getLogger()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", type=str, required=True, help="Input directory to .CONLLUA files")
    parser.add_argument("--output_dir", type=str, required=True, help="Output directory for .jsonlines files")
    parser.add_argument("--segment_size", type=int, default=512)
    parser.add_argument("--tokenizer_name", type=str, default="xlnet-base-cased", help="Tokenizer name")

    parser.add_argument("--ami_dev_file", type=str, default="AMI_dev.CONLLUA")
    parser.add_argument("--ami_test_file", type=str, default="AMI_test.CONLLUA")
    parser.add_argument("--light_dev_file", type=str, default="light_dev.CONLLUA")
    parser.add_argument("--light_test_file", type=str, default="light_test.CONLLUA")
    parser.add_argument("--persuasion_dev_file", type=str, default="Persuasion_dev.CONLLUA")
    parser.add_argument("--persuasion_test_file", type=str, default="Persuasion_test.CONLLUA")
    parser.add_argument("--switchboard_dev_file", type=str, default="Switchboard_3_dev.CONLL")
    parser.add_argument("--switchboard_test_file", type=str, default="Switchboard_test.CONLLUA")

    args = parser.parse_args()
    input_dir = args.input_dir
    out_dir = args.output_dir
    seg_size = args.segment_size
    tok_name = args.tokenizer_name

    input_dataset_names = [
        join(input_dir, args.ami_dev_file),
        join(input_dir, args.ami_test_file),
        join(input_dir, args.light_dev_file),
        join(input_dir, args.light_test_file),
        join(input_dir, args.persuasion_dev_file),
        join(input_dir, args.persuasion_test_file),
        join(input_dir, args.switchboard_dev_file),
        join(input_dir, args.switchboard_test_file)
    ]

    output_dataset_names = [
        join(out_dir, "dev.ami"),
        join(out_dir, "test.ami"),
        join(out_dir, "dev.light"),
        join(out_dir, "test.light"),
        join(out_dir, "dev.persuasion"),
        join(out_dir, "test.persuasion"),
        join(out_dir, "dev.switchboard"),
        join(out_dir, "test.switchboard")
    ]

    for input_dataset_name, output_dataset_name in zip(input_dataset_names, output_dataset_names):
        non_inc_jsonlines_name = output_dataset_name + f'.{seg_size}' + f'.{tok_name}.jsonlines'
        logger.info("Converting {} to {}".format(input_dataset_name, non_inc_jsonlines_name))
        helper.convert_coref_ua_to_json(input_dataset_name,
                                        non_inc_jsonlines_name,
                                        SEGMENT_SIZE=seg_size,
                                        TOKENIZER_NAME=tok_name,
                                        sentences=False)

        sent_inc_jsonlines_name = output_dataset_name + f'.sents.{tok_name}.jsonlines'
        logger.info("Converting {} to {}".format(input_dataset_name, sent_inc_jsonlines_name))
        helper.convert_coref_ua_to_json(input_dataset_name,
                                        sent_inc_jsonlines_name,
                                        TOKENIZER_NAME=tok_name,
                                        sentences=True)

    logger.info("Done processing.")
