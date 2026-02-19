from datetime import datetime
from typing import Optional, List, Union
from hiero_sdk_python.hapi.mirror import consensus_service_pb2 as mirror_proto

def _to_datetime(ts_proto) -> datetime:
    """
    Convert a protobuf Timestamp to a Python datetime (UTC).
    """
    return datetime.utcfromtimestamp(ts_proto.seconds + ts_proto.nanos / 1e9)


class TopicMessageChunk:
    """
    Represents a single chunk within a chunked topic message.
    Mirrors the Java 'TopicMessageChunk'.
    """

    def __init__(self, response: mirror_proto.ConsensusTopicResponse):
        self.consensus_timestamp = _to_datetime(response.consensusTimestamp)
        self.content_size = len(response.message)
        self.running_hash = response.runningHash
        self.sequence_number = response.sequenceNumber


class TopicMessage:
    """
    Represents a Hedera TopicMessage, possibly composed of multiple chunks.
    """

    def __init__(
        self,
        consensus_timestamp: datetime,
        contents: bytes,
        running_hash: bytes,
        sequence_number: int,
        chunks: List[TopicMessageChunk],
        transaction_id: Optional[str] = None,
    ):
        self.consensus_timestamp = consensus_timestamp
        self.contents = contents
        self.running_hash = running_hash
        self.sequence_number = sequence_number
        self.chunks = chunks
        self.transaction_id = transaction_id

    @classmethod
    def of_single(cls, response: mirror_proto.ConsensusTopicResponse) -> "TopicMessage":
        """
        Build a TopicMessage from a single-chunk response.
        """
        chunk = TopicMessageChunk(response)
        consensus_timestamp = chunk.consensus_timestamp
        contents = response.message
        running_hash = response.runningHash
        sequence_number = response.sequence_number

        transaction_id = None
        if response.HasField("chunkInfo") and response.chunkInfo.HasField("initialTransactionID"):
            tx_id = response.chunkInfo.initialTransactionID
            transaction_id = (
                f"{tx_id.shardNum}.{tx_id.realmNum}.{tx_id.accountNum}-"
                f"{tx_id.transactionValidStart.seconds}.{tx_id.transactionValidStart.nanos}"
            )

        return cls(
            consensus_timestamp,
            contents,
            running_hash,
            sequence_number,
            [chunk],
            transaction_id
        )

    @classmethod
    def of_many(cls, responses: List[mirror_proto.ConsensusTopicResponse]) -> "TopicMessage":
        """
        Reassemble multiple chunk responses into a single TopicMessage.
        """
        sorted_responses = sorted(responses, key=lambda r: r.chunkInfo.number)

        chunks = []
        total_size = 0
        transaction_id = None

        for r in sorted_responses:
            c = TopicMessageChunk(r)
            chunks.append(c)
            total_size += len(r.message)

            if (transaction_id is None
                and r.HasField("chunkInfo")
                and r.chunkInfo.HasField("initialTransactionID")):
                tx_id = r.chunkInfo.initialTransactionID
                transaction_id = (
                    f"{tx_id.shardNum}.{tx_id.realmNum}.{tx_id.accountNum}-"
                    f"{tx_id.transactionValidStart.seconds}.{tx_id.transactionValidStart.nanos}"
                )

        contents = bytearray(total_size)
        offset = 0
        for r in sorted_responses:
            end = offset + len(r.message)
            contents[offset:end] = r.message
            offset = end

        last_r = sorted_responses[-1]
        consensus_timestamp = _to_datetime(last_r.consensusTimestamp)
        running_hash = last_r.runningHash
        sequence_number = last_r.sequenceNumber

        return cls(
            consensus_timestamp,
            bytes(contents),
            running_hash,
            sequence_number,
            chunks,
            transaction_id
        )

    @classmethod
    def from_proto(
        cls,
        response_or_responses: Union[mirror_proto.ConsensusTopicResponse, List[mirror_proto.ConsensusTopicResponse]],
        chunking_enabled: bool = False
    ) -> "TopicMessage":
        """
        Creates a TopicMessage from either:
         - A single ConsensusTopicResponse
         - A list of responses (for multi-chunk)

        If chunking is enabled and multiple chunks are detected, they are reassembled
        into one combined TopicMessage. Otherwise, a single chunk is returned as-is.
        """
        if isinstance(response_or_responses, mirror_proto.ConsensusTopicResponse):
            response = response_or_responses
            if chunking_enabled and response.HasField("chunkInfo") and response.chunkInfo.total > 1:
                raise ValueError(
                    "Cannot handle multi-chunk in a single response. Pass all chunk responses in a list."
                )
            return cls.of_single(response)
        else:
            if not response_or_responses:
                raise ValueError("Empty response list provided to from_proto().")

            if not chunking_enabled and len(response_or_responses) == 1:
                return cls.of_single(response_or_responses[0])

            return cls.of_many(response_or_responses)

    def __str__(self):
        contents_str = self.contents.decode("utf-8", errors="replace")
        return (
            f"TopicMessage("
            f"consensus_timestamp={self.consensus_timestamp}, "
            f"sequence_number={self.sequence_number}, "
            f"contents='{contents_str[:40]}{'...' if len(contents_str) > 40 else ''}', "
            f"chunk_count={len(self.chunks)}, "
            f"transaction_id={self.transaction_id}"
            f")"
        )
