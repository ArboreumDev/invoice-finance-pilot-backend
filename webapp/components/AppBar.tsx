import { Box, Button, Center, Flex, HStack, Text } from "@chakra-ui/react";

import React from "react";

// Note: This code could be better, so I'd recommend you to understand how I solved and you could write yours better :)
const AppBar = () => (
  <Flex
    color="black"
    pl="1.5rem"
    pr="1.5rem"
    pb="0.8rem"
    pt="1rem"
    as="nav"
    minH="100px"
    minW="s"
  >
    <Flex align="center">
      <HStack spacing={[5, 10, 20]}>
        <img
          width="190px"
          src="https://app.arboreum.dev/images/logo.svg"
          alt="logo"
        />
      </HStack>
    </Flex>
    <Box flex="1"></Box>
    <HStack className="navButtons">
      {/* <Button size="lg" variant="ghost"> */}
      <Button size="lg" colorScheme="teal">
        Signin (TODO)
      </Button>
      <Button size="lg" colorScheme="teal">
        Sign up
      </Button>
    </HStack>
  </Flex>
);

export default AppBar;
