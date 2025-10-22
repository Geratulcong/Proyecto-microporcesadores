import React from 'react';
import { Container, Row, Col } from 'react-bootstrap';
import ScriptExecutor from '../../components/ScriptExecutor';

const ScriptExecutorPage = () => {
  return (
    <Container fluid>
      <Row>
        <Col>
          <ScriptExecutor />
        </Col>
      </Row>
    </Container>
  );
};

export default ScriptExecutorPage;